// =============================================================================
// THE CLASS BUILD CARDS (2026-09-27)
//
// User: "building builds within classes ... do I want to really have a super
// strong primary or do I want to live off my lethals and tacticals? ... on the
// other map, you could pretty much max out very easily. This one, I want it to be
// a little bit harder ... but I want there to be more upgrades so that you can go
// into your own lane". Answers: ~4 new cards per class, no change to how many
// upgrades a run earns, no lane-mastery bonus.
//
// A run earns ~50-60 upgrade levels (5 altars x 5 + the crown's 3 buys, a deal
// every 4 rounds, trials, the arena); every class held 50-57, so a run maxed
// nearly everything. With these cards each class holds ~80-90, so a good run
// maxes about four or five cards and the rest of the pool is a CHOICE.
//
// EVERY CLASS HAS THREE LANES: WEAPON (the core card + one), KIT (the lethal and
// tactical cards + one that feeds both) and SURVIVAL (the shared cards + one).
// Every new card is 9 levels with its big steps at Lv3 / Lv6 / Lv9 (the user's
// 3/6/9 rule), so an ULTIMATE (+3) always lands one.
//
// THIS MODULE owns the mechanics that sit in the shared lanes, through level
// pointers _tod_upgrades calls (it never imports this file - no cycle):
//   level.tod_cc_damage_fn  - a multiplier on every player hit on an enemy
//                             (upgrade_damage_cb, after the bow's draw):
//                             HUNTER'S MARK (Archer), POINT BLANK (Breacher),
//                             EXECUTIONER (Warrior); JUGGERNAUT's hit stamp.
//   level.tod_cc_dr_fn      - a multiplier on damage the player TAKES (dr_mult):
//                             BULWARK (Breacher), JUGGERNAUT (Warrior).
//   level.tod_cc_kill_fn    - every zombie kill (on_class_gun_kill): POINT BLANK
//                             shells, EXECUTIONER heals, BATTLE RHYTHM.
// SHADOWSTEP (Archer) runs its own per-player damage watcher here. The cards
// that change a class module's own numbers live in that module: REAPER'S REACH /
// PACK MASTER / BURNED OUT (_tod_necro_summon, _tod_necro_skull), AERIALIST
// (_tod_archer), DEMOLITIONIST (_tod_class_kit), BATTLE RHYTHM's extra dash
// (_tod_class_kit).
//
// LOCKSTEP: add_domain rows in _tod_upgrades, ids in _tod_upgrade_ui domain_id,
// tod_upgrade.lua DOMAIN / DETAIL rows (and CoD.TodTextPlate until art lands),
// docs/upgrade_ids.md, both armory pages.
//
// CLASS PASS 2 (2026-09-27, user: "few tweaks to abilities"): POINT BLANK,
// DEMOLITIONIST, AERIALIST, SPRINT FIRE, BURNED OUT, EXECUTIONER, BATTLE RHYTHM and
// JUGGERNAUT left; SOUL SIPHON was parked (the 12-row cap) and retired whole
// 2026-10-05 (W2E; the skull's guarded siphon call is inert). New here:
//   THE PASSIVES - the BREACHER takes no explosive damage, the WARRIOR heals 2% of
//   max health a second, the NECROMANCER is untouchable while cloaked (one front-of-
//   chain player damage callback, immune_damage; the Warrior's regen tick).
//   EXPLOSIVE FUSION (Breacher, 5 levels): C4 / Cluster explosions heal the
//   Breachers standing in them (level.tod_cc_blast_heal_fn, from _tod_class_kit).
//   DEMON SLAYER (Warrior, 9): an elite kill = a timed speed + damage window
//   (level.tod_cc_elite_kill_fn, from tod_bosses::grant_elite_reward - the one seam
//   every elite death reaches; the zombie death-event lane above is inert now).
//   VITALITY (Warrior, 6) and SPRINT (Archer, 9) are read by _tod_upgrades
//   (max_hp_floor, apply_move_speed); the sprint latch lives here (tick).
//   SUMMONER MASTER (Necromancer, 9): a helper kill while at full health raises
//   max health by 1, capped at 4 x Lv x class tier (level.tod_cc_summon_kill_fn,
//   from _tod_necro_summon pay_kill).
//   INVISIBILITY CLOAK (Necromancer, 9, the tactical button, earned by the card):
//   stock's ignoreme refcount + no damage for 3 s + 0.25 s / Lv + 1 s at Lv3/6/9
//   (8.25 s at Lv9), every 60 s - 3 s / Lv (33 s at Lv9)
//   (level.tod_cc_cloak_fire_fn / level.tod_cc_cloak_hud_fn, from _tod_class_kit).
//
// LOGS (dev): [TOD_CARDS] INIT, MARK (applied), SHADOWSTEP, IMMUNE,
// FUSION_HEAL, DEMON, SUMMON_HP, CLOAK_ON / CLOAK_OFF / CLOAK_DENIED, SPRINT.
// =============================================================================

#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\system_shared;
#using scripts\shared\visionset_mgr_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_utility;
#using scripts\zm\zm_tod2_cybercity\_tod_classes;
#using scripts\zm\zm_tod2_cybercity\_tod_upgrades;
#using scripts\zm\zm_tod2_cybercity\_tod_ability_fx;   // docs/203: the ability feedback (both views)

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#namespace tod_class_cards;

// THE CLOAK'S LOOK (2026-09-28): visionset_mgr + the aura clientfield must register in
// the first frame (a system __init__), on both halves - LOCKSTEP _tod_class_cards.csc.
#define TOD_CLOAK_VSMGR            "tod_cloak"
#define TOD_CLOAK_VS_PRIO          92      // unique per type (stock uses <= ~70)
#define TOD_CLOAK_VS_LERP          16
#define TOD_CLOAK_VS_RAMP          0.25    // s in / out of the In Plain Sight vision

REGISTER_SYSTEM( "tod_class_cards", &__init__, undefined )

function __init__()
{
	clientfield::register( "allplayers", "tod_cloak_fx", VERSION_SHIP, 1, "int" );
	visionset_mgr::register_info( "visionset", TOD_CLOAK_VSMGR, VERSION_SHIP, TOD_CLOAK_VS_PRIO, TOD_CLOAK_VS_LERP, true, &visionset_mgr::ramp_in_out_thread_per_player, false );
	visionset_mgr::register_info( "overlay", TOD_CLOAK_VSMGR, VERSION_SHIP, TOD_CLOAK_VS_PRIO, 1, true );
}

#define TOD_CC_BUCKET              3       // the big steps: Lv3 / Lv6 / Lv9

// HUNTER'S MARK (Archer, weapon lane, "huntersmark")
#define TOD_MARK_PCT_LV            0.03    // marked enemies take +3% / Lv from every player (+27% at Lv9)
#define TOD_MARK_MS                5000    // how long a mark lasts ...
#define TOD_MARK_MS_BUCKET         2000    // ... +2 s at Lv3 / Lv6 / Lv9 (11 s)
#define TOD_MARK_FULL_DRAW         2.9     // the draw multiplier that counts as a full draw (x3.0 max)

// SHADOWSTEP (Archer, survival lane, "shadowstep")
#define TOD_SHADOW_MS              1000    // zombies lose you for 1.0 s ...
#define TOD_SHADOW_MS_LV           100     // ... +0.1 s / Lv ...
#define TOD_SHADOW_MS_BUCKET       500     // ... +0.5 s at Lv3 / Lv6 / Lv9 (3.4 s at Lv9)
#define TOD_SHADOW_SPEED           0.20    // +20% move speed for the same window
#define TOD_SHADOW_CD_MS           30000   // cooldown 30 s ...
#define TOD_SHADOW_CD_LV_MS        1500    // ... -1.5 s / Lv (16.5 s at Lv9)

// BULWARK (Breacher, survival lane, "bulwark")
#define TOD_BULWARK_R              200
#define TOD_BULWARK_NEED           3       // zombies within TOD_BULWARK_R that count as "surrounded"
#define TOD_GUARD_PCT_LV           0.02    // -2% damage taken / Lv ...
#define TOD_GUARD_PCT_BUCKET       0.05    // ... -5% more at Lv3 / Lv6 / Lv9 (-33% at Lv9)

// PIERCING (Archer, weapon lane, "pierce", 2026-09-27 CLASS PASS 3 (user)): a direct arrow / bolt hit
// carries on into the zombies behind the target, along the shot's line. The line is as
// wide as the arrow's DEADEYE hit box (gen_tod_twins AXIS.d girth: 8 / 12 / 18 / 24 by
// Deadeye bucket), plus a zombie's half width, so the two cards stack.
#define TOD_PIERCE_RANGE           600     // units behind the struck zombie
#define TOD_PIERCE_PCT_BASE        0.50    // pierced hits deal 50% ...
#define TOD_PIERCE_PCT_LV          0.05    // ... +5% / Lv of the hit (55% at Lv1, 95% at Lv9)
#define TOD_PIERCE_BODY            16      // a zombie's half width
#define TOD_PIERCE_Z               40      // aim at the chest, not the feet

// THE WARRIOR'S PASSIVE: heals 2% of max health every second
#define TOD_WARRIOR_REGEN_PCT      0.02

// DEMON SLAYER (Warrior, weapon lane, "demonslayer"): an elite kill opens a window.
// 9 LEVELS again (user 2026-09-28, after an hour at 6: "make Demon slayer go to 9 levels with a
// small heal portion"): the elite kill also heals a slice of max health, instantly.
#define TOD_DEMON_SPEED_LV         0.02    // +2% move scale / Lv (+18% at Lv9)
#define TOD_DEMON_DMG_LV           0.05    // +5% damage / Lv (+45% at Lv9)
#define TOD_DEMON_MS               6000    // 6 s ...
#define TOD_DEMON_MS_BUCKET        2000    // ... +2 s at Lv3 / Lv6 / Lv9 (12 s)
#define TOD_DEMON_HEAL_PCT_LV      0.02    // heals 2% of max health / Lv on the kill (18% at Lv9)

// EXPLOSIVE FUSION (Breacher, kit lane, "fusion", 9 levels since 2026-09-28 (user)): % of max health per explosion
#define TOD_FUSION_C4_PCT_LV       0.08    // a C4 blast heals 8% / Lv (72% at Lv9)
#define TOD_FUSION_BURST_PCT_LV    0.04    // the Cluster's contact burst 4% / Lv
#define TOD_FUSION_POP_PCT_LV      0.01    // each Cluster bomblet 1% / Lv
#define TOD_FUSION_BODY            32      // stand within the blast radius + this
// ... and THE FUSION JUMP (2026-09-27 class pass 3, user: "explosive fusion allows the breacher
// to gain a massive jump boost when jump from a cluster grenade kinda like fuse in apex.
// This allows for vertical travel"): a Cluster's CONTACT BURST launches every Breacher
// holding the card who stands in it (the bomblets never do). The launch height grows
// per level; the landing takes no fall damage.
#define TOD_FJUMP_H                260     // launch apex 260 u ...
#define TOD_FJUMP_H_LV             40      // ... +40 u / Lv (300 at Lv1, 620 at Lv9; a floor is ~192; was 240 + 60 over 5 levels)
#define TOD_FJUMP_R_ADD            64      // reach: the burst radius + this
#define TOD_FJUMP_GRAVITY          800     // bg_gravity (stock)
#define TOD_FJUMP_GAP_MS           500     // one launch per burst (double-call guard)
// 2026-09-29 (user: "cluster should only send you flying if you jump to avoid players from
// accidentally clustering themselves and getting themselves killed"): a Breacher on the ground
// at the burst is launched only if they JUMP within the grace (the burst lands 50-100 ms after
// the canister touches down, so a jump timed with the throw can fall either side of it).
#define TOD_FJUMP_JUMP_GRACE_MS    250
// ... and ("add a bit of sideways velocity depending on how close to the center you are"): the
// burst pushes you AWAY from it like a rocket jump. The push is strongest at the burst and fades
// to PUSH_EDGE of that at the reach; its SIDEWAYS part is the share of it that points sideways,
// so right over the burst you go straight up and beside it you are thrown out.
#define TOD_FJUMP_PUSH_MAX         480     // u/s of push at the burst's centre
#define TOD_FJUMP_PUSH_EDGE        0.4     // the share of it left at the edge of the reach
#define TOD_FJUMP_CHEST            40      // the push is aimed from the burst to this height above the feet

// SUMMONER MASTER (Necromancer, survival lane, "summonmaster")
#define TOD_SM_HP_PER_KILL         1       // +1 max health per helper kill at full health ...
#define TOD_SM_CAP_LV_TIER         4       // ... up to 4 x Lv x class tier (T1 36 / T2 72 / T3 108 at Lv9)

// INVISIBILITY CLOAK (Necromancer, kit lane, "cloak", the tactical button)
#define TOD_CLOAK_MS               3000
#define TOD_CLOAK_MS_LV            250
#define TOD_CLOAK_MS_BUCKET        1000    // 3.25 s at Lv1 -> 8.25 s at Lv9
#define TOD_CLOAK_CD_MS            60000
#define TOD_CLOAK_CD_LV_MS         3000    // every 57 s at Lv1 -> 33 s at Lv9 (from the press)
// the cloak's vanish / reappear: tod_ability_fx::cloak_on / cloak_off (docs/206: its own cues in both ears + a
// soul burst on the body for the others; the stock Anywhere But Here pair zmb_bgb_abh_teleport_out / _in until then)


function init()
{
	level.tod_cc_damage_fn = &damage_mult;
	level.tod_cc_dr_fn = &taken_mult;
	level.tod_cc_kill_fn = &on_kill;
	level.tod_cc_pierce_fn = &pierce;   // PIERCING, from tod_upgrades::upgrade_damage_cb
	level.tod_cc_blast_heal_fn = &blast_heal;
	level.tod_cc_summon_kill_fn = &summon_kill;
	level.tod_cc_cloak_fire_fn = &cloak_fire;
	level.tod_cc_cloak_hud_fn = &cloak_hud;
	level.tod_cc_elite_kill_fn = &demon_elite_kill;   // DEMON SLAYER, from tod_bosses::grant_elite_reward
	// FIRST in the chain (the _tod_archer / _tod_jumppad pattern): a 0 here ends the
	// hit before any other callback reduces it
	if ( !isdefined( level.player_damage_callbacks ) ) level.player_damage_callbacks = [];
	ArrayInsert( level.player_damage_callbacks, &immune_damage, 0 );
	callback::on_spawned( &on_spawned );
	dev_log( "INIT rev=3 cards=pierce,reaperreach,packmaster,sprint,fusion,demonslayer,vitality,summonmaster,cloak passives=breacher_no_explosive,warrior_regen,archer_sprintfire" );
}

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_CARDS] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function lv( player, key )
{
	return tod_upgrades::get_level( player, key );
}

function bucket( l )
{
	if ( !isdefined( l ) || l <= 0 ) return 0;
	b = Int( l / TOD_CC_BUCKET );
	if ( b > 3 ) b = 3;
	return b;
}

function is_elite( e )
{
	if ( !isdefined( e ) ) return false;
	return ( IS_TRUE( e.is_boss ) || IS_TRUE( e.acc_is_boss ) || IS_TRUE( e.acc_is_mini_boss )
		|| isdefined( e.tod_boss_kind ) );
}

function is_melee_mod( mod )
{
	return ( isdefined( mod ) && IsSubStr( mod, "MELEE" ) );
}

// =============================================================================
// THE DAMAGE LANE: a multiplier on a player's hit on an enemy (self-less).
// =============================================================================
function damage_mult( attacker, victim, weapon, mod, draw_mult )
{
	if ( !isdefined( attacker ) || !isplayer( attacker ) || !isdefined( victim ) )
		return 1.0;
	now = GetTime();
	m = 1.0;

	// HUNTER'S MARK pays EVERY player's hits on a marked enemy (the team card)
	if ( isdefined( victim.tod_mark_until ) && now < victim.tod_mark_until && isdefined( victim.tod_mark_pct ) )
		m += victim.tod_mark_pct;

	cls = attacker.tod_class;
	if ( !isdefined( cls ) )
		return m;
	primary = isdefined( weapon ) && isdefined( tod_classes::gun_for_weapon( attacker, weapon ) );

	if ( cls == "assault" && primary )
	{
		l = lv( attacker, "huntersmark" );
		if ( l > 0 )
		{
			full = IsSubStr( weapon.name, "cc_crossbow" ) || ( isdefined( draw_mult ) && draw_mult >= TOD_MARK_FULL_DRAW );
			if ( full && IsAlive( victim ) )
			{
				pct = TOD_MARK_PCT_LV * l;
				if ( !isdefined( victim.tod_mark_until ) || now >= victim.tod_mark_until || !isdefined( victim.tod_mark_pct ) || victim.tod_mark_pct < pct )
					victim.tod_mark_pct = pct;
				victim.tod_mark_until = now + TOD_MARK_MS + TOD_MARK_MS_BUCKET * bucket( l );
				dev_log( "MARK player=" + attacker GetEntityNumber() + " target=" + victim GetEntityNumber() + " pct=" + victim.tod_mark_pct + " ms=" + ( victim.tod_mark_until - now ) );
			}
		}
	}
	else if ( cls == "slasher" )
	{
		// DEMON SLAYER: every Warrior hit during an elite kill's window
		if ( isdefined( attacker.tod_demon_until ) && now < attacker.tod_demon_until && isdefined( attacker.tod_demon_dmg ) )
			m += attacker.tod_demon_dmg;
	}
	return m;
}

// =============================================================================
// THE ARMOR LANE: a multiplier on damage the player takes (read by dr_mult).
// =============================================================================
function guard_mult( l )
{
	pct = TOD_GUARD_PCT_LV * l + TOD_GUARD_PCT_BUCKET * bucket( l );
	return 1.0 - pct;
}

function taken_mult( player )
{
	if ( !isdefined( player ) || !isplayer( player ) || !isdefined( player.tod_class ) )
		return 1.0;
	now = GetTime();
	m = 1.0;
	if ( player.tod_class == "heavy" )
	{
		l = lv( player, "bulwark" );
		if ( l > 0 && player surrounded() )
			m = m * guard_mult( l );
	}
	return m;
}

// self = player: TOD_BULWARK_NEED or more zombies within TOD_BULWARK_R
function surrounded()
{
	n = 0;
	r2 = TOD_BULWARK_R * TOD_BULWARK_R;
	foreach ( z in GetAITeamArray( level.zombie_team ) )
	{
		if ( !isdefined( z ) || !IsAlive( z ) ) continue;
		if ( DistanceSquared( z.origin, self.origin ) > r2 ) continue;
		n++;
		if ( n >= TOD_BULWARK_NEED ) return true;
	}
	return false;
}

// =============================================================================
// THE KILL LANE: self = the zombie that died, attacker = the player.
// =============================================================================
function on_kill( attacker )
{
	// class pass 2 (2026-09-27): every card that used this lane left (POINT BLANK,
	// EXECUTIONER, BATTLE RHYTHM). DEMON SLAYER rides the elite-reward seam instead
	// (demon_elite_kill below), because not every elite's death reaches the zombie
	// death-event callback that calls this. Kept as the pointer's no-op owner.
	return;
}

// DEMON SLAYER: self = the player who killed an elite (tod_bosses::grant_elite_reward,
// the one place every elite death resolves to exactly one killer; `name` = its kind).
// Any weapon; a partner's kill does not count (that branch returns before the call).
function demon_elite_kill( name )
{
	if ( !isdefined( self ) || !isplayer( self ) || !isdefined( self.tod_class ) || self.tod_class != "slasher" )
		return;
	l = lv( self, "demonslayer" );
	if ( l <= 0 )
		return;
	ms = TOD_DEMON_MS + TOD_DEMON_MS_BUCKET * bucket( l );
	self.tod_demon_speed = TOD_DEMON_SPEED_LV * l;
	self.tod_demon_dmg = TOD_DEMON_DMG_LV * l;
	self.tod_demon_until = GetTime() + ms;
	if ( isdefined( level.tod_apply_speed_fn ) ) self [[ level.tod_apply_speed_fn ]]();
	self thread demon_expire( ms );
	tod_ability_fx::demon_on( self, ms );   // docs/203: the red burst + aura + light on the body, the red edge tint, the demon's cry (it used to be silent and invisible)
	heal = 0;
	hp_before = self.health;
	if ( IsAlive( self ) && !( self laststand::player_is_in_laststand() ) )
	{
		heal = self.maxhealth * TOD_DEMON_HEAL_PCT_LV * l;
		self tod_upgrades::trickle_heal( heal );
	}
	dev_log( "DEMON player=" + self GetEntityNumber() + " elite=" + name + " lv=" + l + " ms=" + ms + " speed=" + self.tod_demon_speed + " dmg=" + self.tod_demon_dmg + " heal=" + heal + " hp=" + hp_before + "->" + self.health + "/" + self.maxhealth );
}

// one re-apply when the window closes, so the speed really ends (newest kill owns it)
function demon_expire( ms )
{
	self notify( "tod_demon_expire" );
	self endon( "tod_demon_expire" );
	self endon( "disconnect" );
	wait ms / 1000.0 + 0.05;
	if ( isdefined( level.tod_apply_speed_fn ) ) self [[ level.tod_apply_speed_fn ]]();
}

// =============================================================================
// SHADOWSTEP: a zombie's hit on an Archer holding the card makes the horde lose
// track of them for a moment (stock's ignoreme refcount) and speeds them up.
// =============================================================================
function on_spawned()
{
	self notify( "tod_cc_respawn" );
	self.tod_cc_speed_until = undefined;
	self.tod_demon_until = undefined;
	self.tod_sprint_hot = undefined;
	self.tod_fjump_air = undefined;
	self thread shadowstep_watch();
	self thread tick();
}

function shadowstep_watch()
{
	self endon( "disconnect" );
	self endon( "tod_cc_respawn" );
	for ( ;; )
	{
		self waittill( "damage", amount, attacker );
		if ( !isdefined( self.tod_class ) || self.tod_class != "assault" ) continue;
		l = lv( self, "shadowstep" );
		if ( l <= 0 ) continue;
		if ( !isdefined( attacker ) || isplayer( attacker ) || !isdefined( attacker.team ) || attacker.team != level.zombie_team ) continue;
		now = GetTime();
		if ( isdefined( self.tod_shadow_next_ms ) && now < self.tod_shadow_next_ms ) continue;
		if ( self laststand::player_is_in_laststand() ) continue;
		ms = TOD_SHADOW_MS + TOD_SHADOW_MS_LV * l + TOD_SHADOW_MS_BUCKET * bucket( l );
		self.tod_shadow_next_ms = now + TOD_SHADOW_CD_MS - TOD_SHADOW_CD_LV_MS * l;
		self thread shadowstep_run( ms );
		dev_log( "SHADOWSTEP player=" + self GetEntityNumber() + " lv=" + l + " ms=" + ms + " next_in=" + ( self.tod_shadow_next_ms - now ) );
	}
}

// Not endon death: the refcount must come back down even if the Archer dies inside the window.
function shadowstep_run( ms )
{
	self zm_utility::increment_ignoreme();
	self.tod_cc_speed = TOD_SHADOW_SPEED;
	self.tod_cc_speed_until = GetTime() + ms;
	if ( isdefined( level.tod_apply_speed_fn ) ) self [[ level.tod_apply_speed_fn ]]();
	wait ms / 1000.0;
	if ( !isdefined( self ) ) return;
	self zm_utility::decrement_ignoreme();
	self.tod_cc_speed_until = undefined;
	if ( isdefined( level.tod_apply_speed_fn ) ) self [[ level.tod_apply_speed_fn ]]();
}

// =============================================================================
// THE PASSIVES: one front-of-chain player damage callback (self = the player).
// 0 = no damage (stock ends the hit); -1 = not ours, the chain continues.
// =============================================================================
function immune_damage( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, psOffsetTime )
{
	if ( !isdefined( iDamage ) || iDamage <= 0 || !isdefined( self.tod_class ) )
		return -1;
	// INVISIBILITY CLOAK: nothing hurts a cloaked Necromancer
	if ( isdefined( self.tod_cloak_until ) && GetTime() < self.tod_cloak_until )
	{
		self immune_log( "cloak", sMeansOfDeath, iDamage );
		return 0;
	}
	// THE FUSION JUMP lands without fall damage
	if ( IS_TRUE( self.tod_fjump_air ) && sMeansOfDeath == "MOD_FALLING" )
	{
		self immune_log( "fusion_jump_landing", sMeansOfDeath, iDamage );
		return 0;
	}
	// THE BREACHER'S PASSIVE: no explosive damage, from anyone
	if ( self.tod_class == "heavy" && is_explosive_mod( sMeansOfDeath ) )
	{
		self immune_log( "breacher_explosive", sMeansOfDeath, iDamage );
		return 0;
	}
	return -1;
}

function is_explosive_mod( mod )
{
	return ( isdefined( mod ) && ( mod == "MOD_GRENADE" || mod == "MOD_GRENADE_SPLASH" || mod == "MOD_EXPLOSIVE" || mod == "MOD_PROJECTILE_SPLASH" ) );
}

// throttled: at most one line a second per player
function immune_log( why, mod, dmg )
{
	now = GetTime();
	if ( isdefined( self.tod_immune_log_ms ) && now < self.tod_immune_log_ms ) return;
	self.tod_immune_log_ms = now + 1000;
	dev_log( "IMMUNE player=" + self GetEntityNumber() + " why=" + why + " mod=" + mod + " dmg=" + dmg );
}

// =============================================================================
// THE PER-PLAYER TICK (0.1 s): the Archer's SPRINT latch; the Warrior's regen.
// =============================================================================
function tick()
{
	self endon( "disconnect" );
	self endon( "tod_cc_respawn" );
	level endon( "end_game" );
	n = 0;
	for ( ;; )
	{
		wait 0.1;
		n++;
		if ( !isdefined( self.tod_class ) ) continue;
		// SPRINT (Archer): the card's speed counts only while sprinting
		hot = ( self.tod_class == "assault" && lv( self, "sprint" ) > 0 && self IsSprinting() );
		if ( hot != IS_TRUE( self.tod_sprint_hot ) )
		{
			self.tod_sprint_hot = hot;
			if ( isdefined( level.tod_apply_speed_fn ) ) self [[ level.tod_apply_speed_fn ]]();
		}
		// THE WARRIOR'S PASSIVE: 2% of max health every second
		if ( n % 10 == 0 && self.tod_class == "slasher" && IsAlive( self ) && !( self laststand::player_is_in_laststand() )
			&& isdefined( self.maxhealth ) && self.health < self.maxhealth )
		{
			hp = Int( self.maxhealth * TOD_WARRIOR_REGEN_PCT + 0.999 );
			self tod_upgrades::trickle_heal( hp );
		}
	}
}

// =============================================================================
// EXPLOSIVE FUSION (Breacher): an explosion at org heals every Breacher holding
// the card who stands inside it. kind = "c4" / "burst" / "pop" (_tod_class_kit).
// =============================================================================
function blast_heal( org, radius, kind )
{
	if ( !isdefined( org ) || !isdefined( radius ) ) return;
	pct_lv = TOD_FUSION_POP_PCT_LV;
	if ( kind == "c4" ) pct_lv = TOD_FUSION_C4_PCT_LV;
	else if ( kind == "burst" ) pct_lv = TOD_FUSION_BURST_PCT_LV;
	r = radius + TOD_FUSION_BODY;
	rj = radius + TOD_FJUMP_R_ADD;
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || !isdefined( p.tod_class ) || p.tod_class != "heavy" ) continue;
		l = lv( p, "fusion" );
		if ( l <= 0 || !IsAlive( p ) || p laststand::player_is_in_laststand() ) continue;
		// THE FUSION JUMP: the Cluster's contact burst only (never the bomblets or C4), and only
		// for a Breacher who jumps (fusion_jump_try)
		if ( kind == "burst" && DistanceSquared( p.origin, org ) <= rj * rj )
			p thread fusion_jump_try( org, l, rj );
		if ( DistanceSquared( p.origin, org ) > r * r ) continue;
		if ( !isdefined( p.maxhealth ) || p.health >= p.maxhealth ) continue;
		hp = Int( p.maxhealth * pct_lv * l + 0.999 );
		p tod_upgrades::trickle_heal( hp );
		tod_ability_fx::fusion_heal( p );   // docs/203: an ember shower on the body, an orange flash on the screen, the heal cue (once per blast)
		dev_log( "FUSION_HEAL player=" + p GetEntityNumber() + " kind=" + kind + " lv=" + l + " hp=" + hp + " now=" + p.health + "/" + p.maxhealth );
	}
}

// THE JUMP GATE (2026-09-29): self = a Breacher inside the burst's reach. Airborne at the
// burst = launch now; on the ground = launch only if they leave it within
// TOD_FJUMP_JUMP_GRACE_MS (a jump timed with the throw); otherwise no launch, so a Breacher
// standing in their own Cluster is never thrown off the tower. One try per burst.
function fusion_jump_try( org, l, reach )
{
	self endon( "disconnect" );
	self endon( "death" );
	now = GetTime();
	if ( isdefined( self.tod_fjump_ms ) && now - self.tod_fjump_ms < TOD_FJUMP_GAP_MS ) return;
	self.tod_fjump_ms = now;
	why = self fusion_jump_blocked();
	if ( isdefined( why ) )
	{
		dev_log( "FUSION_JUMP_SKIP player=" + self GetEntityNumber() + " reason=" + why );
		return;
	}
	waited = 0;
	if ( self IsOnGround() )
	{
		while ( waited < TOD_FJUMP_JUMP_GRACE_MS && isdefined( self ) && self IsOnGround() )
		{
			wait 0.05;
			waited += 50;
		}
		if ( !isdefined( self ) ) return;
		if ( self IsOnGround() )
		{
			dev_log( "FUSION_JUMP_SKIP player=" + self GetEntityNumber() + " reason=no_jump (on the ground " + TOD_FJUMP_JUMP_GRACE_MS + " ms after the burst)" );
			return;
		}
		why = self fusion_jump_blocked();
		if ( isdefined( why ) )
		{
			dev_log( "FUSION_JUMP_SKIP player=" + self GetEntityNumber() + " reason=" + why );
			return;
		}
	}
	self fusion_jump( org, l, reach, waited );
}

// -> undefined when the launch may run, else why not. The jump pad owns a flyer's body
// (_tod_jumppad.gsc: every feature that moves the player refuses while it flies).
function fusion_jump_blocked()
{
	if ( !IsAlive( self ) || self laststand::player_is_in_laststand() ) return "down";
	if ( IS_TRUE( self.tod_jumppad_flying ) ) return "jumppad";
	if ( self IsMantling() ) return "mantle";
	if ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( self.tod_menu_frozen ) ) return "frozen";
	return undefined;
}

// THE FUSION JUMP: self = the Breacher, org = the burst. The launch replaces the vertical
// speed with the card's apex and ADDS the burst's push (see the defines) to the run speed the
// player already had. SetVelocity with positive z is discarded while IsOnGround, so lift the
// origin 1 unit first (stock _zm_jump_pad / _tod_archer::floor_release; after the jump gate
// the player is normally airborne already).
function fusion_jump( org, l, reach, waited )
{
	h = TOD_FJUMP_H + TOD_FJUMP_H_LV * l;
	vz = Sqrt( 2 * TOD_FJUMP_GRAVITY * h );
	vel = self GetVelocity();
	push = fusion_push( self.origin, org, reach );
	out = ( vel[ 0 ] + push[ 0 ], vel[ 1 ] + push[ 1 ], vz );
	if ( self IsOnGround() ) self SetOrigin( self.origin + ( 0, 0, 1 ) );
	self SetVelocity( out );
	self.tod_fjump_air = true;
	self.tod_fjump_launch_ms = GetTime();   // the Breacher's air steering re-anchors on a launch
	self thread fusion_jump_land();
	tod_ability_fx::fusion_launch( self );   // docs/203: the rocket burst under the feet, the ember trail in the air, the jet whoosh in both ears
	dev_log( "FUSION_JUMP player=" + self GetEntityNumber() + " lv=" + l + " apex=" + h + " vz=" + Int( vz ) + " dist=" + Int( Distance( self.origin, org ) ) + " push=" + Int( Length( push ) ) + " speed_out=" + Int( Length( ( out[ 0 ], out[ 1 ], 0 ) ) ) + " jump_wait_ms=" + waited );
}

// -> the burst's sideways push on a body at feet: away from the burst, strongest at it
// (TOD_FJUMP_PUSH_MAX, fading linearly to PUSH_EDGE of that at the reach), and only the part
// of it that points sideways (flat / distance): straight over the burst it is zero.
function fusion_push( feet, org, reach )
{
	dx = feet[ 0 ] - org[ 0 ];
	dy = feet[ 1 ] - org[ 1 ];
	dz = ( feet[ 2 ] + TOD_FJUMP_CHEST ) - org[ 2 ];
	flat = Sqrt( ( dx * dx ) + ( dy * dy ) );
	d3 = Sqrt( ( flat * flat ) + ( dz * dz ) );
	if ( flat < 1 || d3 < 1 || reach <= 0 ) return ( 0, 0, 0 );
	t = d3 / reach;
	if ( t > 1 ) t = 1;
	strength = TOD_FJUMP_PUSH_MAX * ( 1 - ( ( 1 - TOD_FJUMP_PUSH_EDGE ) * t ) );
	side = strength * ( flat / d3 );
	return ( ( dx / flat ) * side, ( dy / flat ) * side, 0 );
}

// fall-damage immunity from the launch until 0.25 s after the landing (immune_damage)
function fusion_jump_land()
{
	self notify( "tod_fjump_land" );
	self endon( "tod_fjump_land" );
	self endon( "disconnect" );
	t = 0;
	while ( t < 0.5 && isdefined( self ) && self IsOnGround() ) { wait 0.05; t += 0.05; }   // leave the floor
	t = 0;
	while ( t < 8 && isdefined( self ) && !( self IsOnGround() ) ) { wait 0.05; t += 0.05; }   // come down
	if ( isdefined( self ) ) tod_ability_fx::fusion_land( self );   // docs/203: the dust ring + thud, the trail ends (the air was silent and invisible)
	wait 0.25;
	if ( !isdefined( self ) ) return;
	self.tod_fjump_air = undefined;
	dev_log( "FUSION_LAND player=" + self GetEntityNumber() + " air_s=" + t );
}

// =============================================================================
// SUMMONER MASTER (Necromancer): self = the owner of a helper that just killed.
// Only at full health; the bank is read by tod_upgrades::max_hp_floor.
// =============================================================================
function summon_kill()
{
	if ( !isdefined( self.tod_class ) || self.tod_class != "necromancer" ) return;
	l = lv( self, "summonmaster" );
	if ( l <= 0 || !IsAlive( self ) || self laststand::player_is_in_laststand() ) return;
	if ( !isdefined( self.maxhealth ) || self.health < self.maxhealth ) return;
	tier = ( isdefined( self.tod_tier ) ? self.tod_tier : 1 );
	cap = TOD_SM_CAP_LV_TIER * l * tier;
	if ( !isdefined( self.tod_summon_hp ) ) self.tod_summon_hp = 0;
	if ( self.tod_summon_hp >= cap ) return;
	self.tod_summon_hp = Int( Min( cap, self.tod_summon_hp + TOD_SM_HP_PER_KILL ) );
	// raise max AND health together: the player was full, and must stay full or the
	// next kill would not count
	want = self tod_upgrades::max_hp_floor();
	if ( self.maxhealth < want )
	{
		self.maxhealth = want;
		self SetMaxHealth( want );
	}
	self.health = self.maxhealth;
	if ( self.tod_summon_hp <= 3 || self.tod_summon_hp % 10 == 0 || self.tod_summon_hp == cap )
		dev_log( "SUMMON_HP player=" + self GetEntityNumber() + " lv=" + l + " tier=" + tier + " bank=" + self.tod_summon_hp + "/" + cap + " max=" + self.maxhealth );
}

// =============================================================================
// INVISIBILITY CLOAK (Necromancer): the tactical press (self = the player).
// =============================================================================
function cloak_ms( l )    { return TOD_CLOAK_MS + TOD_CLOAK_MS_LV * l + TOD_CLOAK_MS_BUCKET * bucket( l ); }
function cloak_cd_ms( l ) { return TOD_CLOAK_CD_MS - TOD_CLOAK_CD_LV_MS * l; }

function cloak_fire( unlimited )
{
	l = lv( self, "cloak" );
	now = GetTime();
	why = "";
	if ( l <= 0 ) why = "locked_no_card";
	else if ( isdefined( self.tod_cloak_until ) && now < self.tod_cloak_until ) why = "already_cloaked";
	else if ( !IS_TRUE( unlimited ) && isdefined( self.tod_cloak_next_ms ) && now < self.tod_cloak_next_ms ) why = "cooldown";
	if ( why != "" )
	{
		dev_log( "CLOAK_DENIED player=" + self GetEntityNumber() + " reason=" + why + ( why == "cooldown" ? " left_ms=" + ( self.tod_cloak_next_ms - now ) : "" ) );
		tod_ability_fx::kit_deny( self, "cloak", why );   // PK18: a refused press is heard
		return;
	}
	ms = cloak_ms( l );
	self.tod_cloak_next_ms = now + cloak_cd_ms( l );
	self thread cloak_run( ms );
	dev_log( "CLOAK_ON player=" + self GetEntityNumber() + " lv=" + l + " ms=" + ms + " next_in=" + ( self.tod_cloak_next_ms - now ) );
}

// Not endon death: the refcount must come back down whatever happens (Shadowstep's rule).
function cloak_run( ms )
{
	self zm_utility::increment_ignoreme();
	self.tod_cloak_until = GetTime() + ms;
	tod_ability_fx::cloak_on( self );
	// the look: In Plain Sight on the cloaked player's screen, a soul aura for everyone else
	full = ms / 1000.0 - 2 * TOD_CLOAK_VS_RAMP;
	if ( full < 0.05 ) full = 0.05;
	visionset_mgr::activate( "visionset", TOD_CLOAK_VSMGR, self, TOD_CLOAK_VS_RAMP, full, TOD_CLOAK_VS_RAMP );
	visionset_mgr::activate( "overlay", TOD_CLOAK_VSMGR, self );
	self clientfield::set( "tod_cloak_fx", 1 );
	wait ms / 1000.0;
	if ( !isdefined( self ) ) return;
	self zm_utility::decrement_ignoreme();
	self.tod_cloak_until = undefined;
	visionset_mgr::deactivate( "overlay", TOD_CLOAK_VSMGR, self );
	self clientfield::set( "tod_cloak_fx", 0 );
	tod_ability_fx::cloak_off( self );
	dev_log( "CLOAK_OFF player=" + self GetEntityNumber() );
}

// the HUD's tactical tile (LOCKSTEP AetheriumLoadout CLASS_KITS[3]):
// -2 no card, -1 cloaked, 0 ready, N seconds to ready
function cloak_hud( unlimited )
{
	l = lv( self, "cloak" );
	if ( l <= 0 ) return -2;
	now = GetTime();
	if ( isdefined( self.tod_cloak_until ) && now < self.tod_cloak_until ) return -1;
	if ( IS_TRUE( unlimited ) || !isdefined( self.tod_cloak_next_ms ) || now >= self.tod_cloak_next_ms ) return 0;
	return Int( ( self.tod_cloak_next_ms - now ) / 1000 + 0.999 );
}

// =============================================================================
// PIERCING (Archer): self = the zombie the arrow hit. The pierced zombies take a
// share of `dmg` through the tod_cleave_hit pass-through (no re-pierce, no card
// re-multiply, no second power scale); walls stop the pierce.
// =============================================================================
function pierce_girth( player )
{
	b = bucket( lv( player, "deadeye" ) );
	return ( ( b >= 3 ) ? 24 : ( ( b == 2 ) ? 18 : ( ( b == 1 ) ? 12 : 8 ) ) );   // LOCKSTEP gen_tod_twins AXIS.d girth (bows' base 8)
}

function is_direct_mod( mod )
{
	return ( isdefined( mod ) && ( mod == "MOD_PROJECTILE" || mod == "MOD_IMPALE" || mod == "MOD_RIFLE_BULLET" || mod == "MOD_PISTOL_BULLET" ) );
}

function pierce( attacker, weapon, dmg, vdir, mod )
{
	if ( !isdefined( attacker ) || !isplayer( attacker ) || !isdefined( weapon ) || !isdefined( dmg ) || dmg <= 0 ) return;
	l = lv( attacker, "pierce" );
	if ( l <= 0 || !is_direct_mod( mod ) ) return;
	if ( !isdefined( tod_classes::gun_for_weapon( attacker, weapon ) ) ) return;   // the class bow / crossbow only
	n = 1 + bucket( l );   // 1 / 2 / 3 / 4 zombies at Lv1 / Lv3 / Lv6 / Lv9
	dir = undefined;
	if ( isdefined( vdir ) && Length( vdir ) > 0.001 ) dir = VectorNormalize( vdir );
	else dir = VectorNormalize( self.origin - attacker.origin );
	p0 = self.origin + ( 0, 0, TOD_PIERCE_Z );
	r = TOD_PIERCE_BODY + pierce_girth( attacker );
	hits = [];
	ts = [];
	foreach ( z in GetAITeamArray( level.zombie_team ) )
	{
		if ( !isdefined( z ) || z == self || !IsAlive( z ) ) continue;
		v = ( z.origin + ( 0, 0, TOD_PIERCE_Z ) ) - p0;
		t = VectorDot( v, dir );
		if ( t <= 0 || t > TOD_PIERCE_RANGE ) continue;
		if ( Length( v - dir * t ) > r ) continue;
		// keep the nearest n, in order along the line
		i = hits.size;
		while ( i > 0 && ts[ i - 1 ] > t ) { hits[ i ] = hits[ i - 1 ]; ts[ i ] = ts[ i - 1 ]; i--; }
		hits[ i ] = z;
		ts[ i ] = t;
	}
	if ( hits.size == 0 ) return;
	share = Int( dmg * ( TOD_PIERCE_PCT_BASE + TOD_PIERCE_PCT_LV * l ) + 0.5 );
	if ( share < 1 ) share = 1;
	done = 0;
	foreach ( z in hits )
	{
		if ( done >= n ) break;
		if ( !isdefined( z ) || !IsAlive( z ) ) continue;
		to = z.origin + ( 0, 0, TOD_PIERCE_Z );
		if ( !BulletTracePassed( p0, to, false, self ) ) break;   // a wall stops the arrow
		z.tod_cleave_hit = true;
		tod_ability_fx::pierce_hit( z );   // docs/206: the through-hit the party sees + hears (before the damage: the zombie may die of it)
		z DoDamage( share, to, attacker, attacker, "none", mod, 0, weapon );
		if ( isdefined( z ) && IS_TRUE( z.tod_cleave_hit ) ) z.tod_cleave_hit = undefined;
		done++;
	}
	if ( done > 0 )
		dev_log( "PIERCE player=" + attacker GetEntityNumber() + " lv=" + l + " weapon=" + weapon.name + " hit=" + done + "/" + n + " share=" + share + " of " + Int( dmg ) + " r=" + r );
}

