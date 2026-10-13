// =============================================================================
// _tod_necro_summon.gsc — THE NECROMANCER'S HELPERS + SOUL BOMB (2026-09-26).
//
// User: "The left button ... the aiming button. I want that to summon helpers ...
// better helpers as your tier increases"; "tier one can be zombies. Tier two can
// definitely be some soul hounds ... a blue grayish aura instead of that fire
// aura ... tier three ... let's do mangler for now"; "soul bomb ... a blast of
// souls that comes out of your player ... soul-like, not electricity-like".
//
// HOLD AIM ON A ZOMBIE (user 2026-09-26: "you should have to use it on a zombie ...
// use the current damage effects for the summoning ... it kind of lifts the zombies
// and then it turns them into one of your helpers"). The skull's torch picks the
// ordinary zombie nearest your crosshair (TOD_BIND_DOT, TOD_SUMMON_REACH, line of
// sight; never an elite) and souls flow INTO it (actor state 3: the client streams
// wisps from you to it) and it is LIFTED FOR THE WHOLE BIND: the death-ray lift anim
// (1.5 s, does not loop) played SLOWED to last exactly bind_ms() (user 2026-09-26: "the
// zombie can keep running at me until ... the animation. It would be great if it can
// get in that animation the whole time ... slow down the animation so it sticks to the
// same length"); after bind_ms() of holding it on the crosshair (TOD_BIND_MS 7.2 s, SUMMONING POWER cuts
// it TOD_POWER_BIND_STEP / Lv - user 2026-09-26: "supposed to take a long time ...
// the upgrade is that it takes less and less time") it becomes your helper and the
// soul meter pays. Let go, fire, or lose
// it from the crosshair and it drops back into the horde. Keep holding to bind the
// next one TOD_SUMMON_REPEAT_MS later while slots and souls last. The helper type
// is the CLASS TIER (the skull is the gun on every tier):
//   tier 1  THRALLS      up to 3: THAT ZOMBIE, turned to your side through stock's
//                        own TURNED path (team "allies" + aat_turned: the zombie
//                        tree finds a zombie enemy and every swing KILLS an
//                        ordinary zombie - zombie.gsc zombieNotetrackMeleeFire).
//   tier 2  SOUL HOUNDS  up to 3: stock hellhounds on your side, NO fire (dog_fx is
//                        never set) - a blue-grey soul body instead. Fast; a bite
//                        kills an ordinary zombie, elites take a bite's worth.
//   tier 3  THE MANGLER  one, plus up to 2 soul hounds while it lives. Hellbound's
//                        default Mangler on your side: melee sweeps and its cannon.
// Tiers 2 and 3 tear the lifted zombie's soul out and the hound / Mangler rises
// from its body.
// Helpers live TOD_*_LIFE unpaused seconds (thralls also end at their kill limit,
// stock Turned's rule), then burst into souls. Nothing on the horde's side attacks
// them (zombies hunt players), so their "health" is their life span. Every kill a
// helper makes pays you TOD_SUMMON_KILL_PTS and TOD_SUMMON_REFUND soul meter.
// THE WHITE BAR (user 2026-10-01: "the necromancers summoners need to have the white
// bar. So you can tell the difference and you can see how much health they have
// left"): every helper wears a WHITE over-head bar (_tod_elite_hp, set s; elites wear
// RED). helper_life publishes what is left of the helper as tod_hpbar_frac (0..1):
// the life clock, and for a thrall its kills too - whichever runs out first.
//
// THE SOUL PULSE (was "Soul Bomb"; the internal key and TOD_BOMB_* names stay) - the
// lethal button, _tod_class_kit.gsc polls it: souls rush out from the Necromancer and a
// flat white ring sweeps along the floor to the kill edge (_tod_necro_skull.csc). Every
// ordinary zombie within TOD_BOMB_RADIUS has its soul torn out (dies, refunds meter);
// elites take TOD_BOMB_ELITE round-zombie healths. Each dies as the ring passes it:
// the ring reaches the edge in TOD_BOMB_WAVE_MS, so a victim waits wave x dist/radius. It is CHARGED BY SOULS, not a timer: every kill
// you make (beam souls, helper kills, drained elites, Burned Out) adds one, and it
// is ready at bomb_souls_need(): TOD_BOMB_ROUND_PCT of the ROUND's zombies (stock's
// count for the round and party size, so it grows with the rounds AND with co-op),
// the SOUL BOMB card taking TOD_BOMB_PCT_STEP off per level, never under
// TOD_BOMB_SOULS_MIN. Kills carry over when the round (and the need) moves. Its
// own kills and binds add nothing. Dev's unlimited offhand skips the charge.
//
// FX are stock soul effects recoloured blue-grey by tools/necromancer/make_soul_fx.py
// (share/raw/fx/tod/necro/). Auras ride the actor field "tod_necro_soul"
// (registered in _tod_necro_skull.gsc): 1 soul torn out (one-shot), 3 being bound
// (the lift), 5 thrall, 6 soul hound, 7 Mangler. LOCKSTEP with _tod_necro_skull.csc.
// (The 2026-09-26 thrall RISE at the aim point - a level.zombie_custom_think_logic
// hook that handed stock's rise a spot - is RETIRED WHOLE: a thrall is a zombie you
// bound, so nothing spawns for tier 1 and no global spawn hook is installed.)
//
// LOGS [TOD_NECRO_SUMMON] under tod_dev: INIT, BIND (start: target, kind, ms, power
// lv, meter), BIND_LIFT (at_ms of_ms), BIND_CANCEL (why, held_ms), SUMMON (kind,
// how=turned/body, tier, meter), DENY (why: slots / meter / actor_budget /
// spawn_failed), HELPER_KILL, HELPER_END (why, life, kills), SOULS +1 (src, total,
// need), BOMB ready, BOMB spent (killed, elites), BOMB_DENY (souls, need).
// =============================================================================

#using scripts\codescripts\struct;
#using scripts\shared\ai\systems\gib;
#using scripts\shared\ai\zombie_utility;
#using scripts\shared\animation_shared;
#using scripts\shared\array_shared;
#using scripts\shared\callbacks_shared;
#using scripts\shared\clientfield_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\scene_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_score;
#using scripts\zm\_zm_spawner;
#using scripts\zm\_zm_utility;
#using scripts\zm\zm_tod2_cybercity\_tod_mangler;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;
#using scripts\zm\zm_tod2_cybercity\_tod_ability_fx;   // docs/203: the ability feedback (both views)

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#insert scripts\shared\ai\systems\gib.gsh;

#using_animtree( "generic" );

#precache( "model", "tag_origin" );
#precache( "xmodel", "tod_necro_thrall_head" );   // the thrall's black, white-eyed head
#precache( "xmodel", "tod_necro_thrall_body" );   // the black helper models (tools/necromancer/make_helper_models.py)
#precache( "xmodel", "tod_necro_hound" );
#precache( "xmodel", "tod_necro_mangler" );
#precache( "fx", "tod/necro/fx_necro_soul_bomb" );
#precache( "fx", "tod/necro/fx_necro_summon" );
#precache( "fx", "tod/necro/fx_necro_soul_rip" );
#precache( "fx", "tod/necro/fx_necro_mgl_shot" );
#precache( "fx", "tod/necro/fx_necro_mgl_blast" );

#namespace tod_necro_summon;

#define TOD_NECRO_CLASS           "necromancer"
#define TOD_NECRO_STEM            "tod_necro_skull"
#define TOD_SUMMON_METER_MAX      100      // LOCKSTEP _tod_necro_skull TOD_NECRO_METER_MAX

// ---- summoning ----------------------------------------------------------------
#define TOD_BIND_MS               7200     // hold a zombie this long to bind it: 1200 -> 3600 (user 2026-09-26: "three times as longer") -> 7200 (same day: "needs to be 2x. Its still too quick")
#define TOD_BIND_LIFT_MS          1500     // the lift anim is 45 frames @ 30 = 1.5 s and does not loop: played at rate LIFT_MS / bind_ms it spans the whole bind
#define TOD_BIND_ANIM             "ai_zm_dlc1_zombie_dth_deathray_4"   // the lift - the anim inside TOD_BIND_SCENE, played by name the way the scene system does (animation::play)
#define TOD_BIND_DOT              0.9      // pick: the zombie nearest the crosshair inside this cone ...
#define TOD_BIND_HOLD_DOT         0.75     // ... and it stays bound a little wider
#define TOD_BIND_MAX_MS           12000    // a bind nobody finishes lets go (a guard above the longest bind, never reached by play)
#define TOD_BIND_SCENE            "cin_zm_dlc1_zombie_dth_deathray_04"   // the zoned scriptbundle that loads TOD_BIND_ANIM (kept zoned for that)
#define TOD_BIND_HOLD_RATE        0.01     // the held lift: the clip slowed to this IN THE AIR (bind_hold_keep), never restarted - a restart put the zombie back on the floor (user 2026-10-05)
#define TOD_SUMMON_REPEAT_MS      900      // after a helper, the next bind can start this much later
#define TOD_SUMMON_REACH          600      // how far the skull reaches for a zombie to bind
#define TOD_SUMMON_ACTOR_RESERVE  4        // never take the last free actor slots
#define TOD_SUMMON_KILL_PTS       50       // points per helper kill (the partners' rate)
#define TOD_SUMMON_REFUND         2        // soul meter per helper kill
#define TOD_SUMMON_LEASH          1400     // a helper further than this from you comes back
#define TOD_SUMMON_SEEK           900      // helpers pick zombies this close to themselves ...
#define TOD_SUMMON_SEEK_OWNER     1100     // ... and this close to you
#define TOD_HELPER_BLINK_S        6        // a helper unmoved this many seconds (goal > 150 away, not attacking) blinks beside you in a soul burst

#define TOD_THRALL_MAX            3
#define TOD_THRALL_COST           25
#define TOD_THRALL_LIFE           25       // s (stock Turned: 20)
#define TOD_THRALL_KILLS          12       // stock Turned's kill limit
// THE HELPERS ARE THEIR OWN MODELS (user 2026-09-26: "they look too close to the actual enemies ... a complete
// black model with white eyes ... these should be different models from the enemy models"): the enemy mesh +
// skeleton wearing black twins of every material (make_helper_models.py). The thrall is re-skinned on the turn.
#define TOD_THRALL_BODY           "tod_necro_thrall_body"   // the charcoal body, black
#define TOD_THRALL_BODY_DONOR     "tod_charcoal_c_zom_dlc3_zombie_sentinel_body"   // the only body the charcoal horde wears; any other body is kept (logged)
#define TOD_THRALL_HEAD           "tod_necro_thrall_head"   // the charcoal head, black, white eyes
#define TOD_THRALL_HEAD_DONOR     "tod_charcoal_c_zom_dlc4_zombie_charred_head"   // the only head the charcoal horde wears; any other head is kept (logged)

#define TOD_HOUND_MAX             3
#define TOD_HOUND_MODEL           "tod_necro_hound"         // the stock hellhound, black, white eyes
#define TOD_HOUND_MAX_T3          2        // beside the Mangler
#define TOD_HOUND_COST            30
#define TOD_HOUND_LIFE            30
#define TOD_HOUND_BITE_RANGE      80
#define TOD_HOUND_BITE_MS         700
#define TOD_HOUND_ELITE_BITE      1.0      // round-zombie healths per bite on an elite

#define TOD_MANGLER_MAX           1
#define TOD_MANGLER_MODEL         "tod_necro_mangler"       // Hellbound's BO6 Mangler, black (its white eye glow is the client fx)
#define TOD_MANGLER_SHOT_FX       "tod/necro/fx_necro_mgl_shot"    // the cannon's shot + blast, soul-coloured (the enemy keeps the orange ones)
#define TOD_MANGLER_BLAST_FX      "tod/necro/fx_necro_mgl_blast"
#define TOD_MANGLER_COST          60
#define TOD_MANGLER_LIFE          35
#define TOD_MANGLER_MELEE_RANGE   100
#define TOD_MANGLER_SWEEP         130
#define TOD_MANGLER_MELEE_ELITE   3.0
#define TOD_MANGLER_CANNON_MS     4000
#define TOD_MANGLER_CANNON_RANGE  800
#define TOD_MANGLER_BLAST         180
#define TOD_MANGLER_CANNON_ELITE  3.0

// ---- the soul bomb ------------------------------------------------------------
#define TOD_BOMB_RADIUS           360
#define TOD_BOMB_ROUND_PCT        0.50     // souls (your kills) to charge it = this share of the ROUND's zombies (user 2026-09-26: "proportionate to the round ... factor in co-op")
#define TOD_BOMB_SOULS_MIN        3        // never fewer souls than this (round 1 solo = 6 zombies -> 3)
#define TOD_BOMB_ROUND_FALLBACK   24       // the round total if _tod_luck has not published one yet (stock's base)
#define TOD_BOMB_ELITE            2.0      // round-zombie healths to an elite
#define TOD_BOMB_REFUND           3        // soul meter per soul torn out (= the beam's)
#define TOD_BOMB_WAVE_MS          140      // the ring reaches the kill edge this long after the cast; a victim dies as it passes (LOCKSTEP make_soul_fx RING_LIFE_MS x RING_REACH)
#define TOD_BOMB_RING_R0          360      // the ring bands (LOCKSTEP make_soul_fx RING_RADII 360/440/520/600): band = nearest
#define TOD_BOMB_RING_STEP        80

// actor field "tod_necro_soul" states owned here
#define TOD_SOUL_RIP              1
#define TOD_SOUL_BIND             3
#define TOD_SOUL_THRALL           5
#define TOD_SOUL_HOUND            6
#define TOD_SOUL_MANGLER          7

// ---- the Necromancer's class cards (2026-09-26, user: "complete the upgrades") --
// Read off the player's card levels (the table tod_upgrades::get_level reads).
// LOCKSTEP with tod_upgrade.lua DETAIL rows 59 / 38 / 39 (the card text).
// 2026-09-27 (user: "level nine as max" / "standardize this 3,6,9 level process"):
// every Necromancer card is 9 levels with its big steps at Lv3 / Lv6 / Lv9, and an
// ULTIMATE (+3) always crosses one. Per-level steps are re-cut so Lv9 lands where Lv8 did.
// SOUL PULSE (id 59, "soulbomb", max 9)
#define TOD_CARD_BOMB_MAX         9
#define TOD_BOMB_PCT_STEP         0.0222   // -2.2 points of the round's share / Lv: 50% -> 30% at Lv9
#define TOD_BOMB_RADIUS_STEP      80       // BUCKETS: 360 -> 440 / 520 / 600 at Lv3 / Lv6 / Lv9 (= the ring bands)
#define TOD_BOMB_ELITE_STEP       4.5      // elite hit 2 -> 6.5 round zombies' health, on the LOG curve (card_curve) - every level adds, early levels the most (user 2026-09-28)
// SUMMONING POWER (id 38, "summonpower", max 9)
#define TOD_CARD_POWER_MAX        9
#define TOD_POWER_SLOT_LV1        3        // +1 thrall / hound slot at Lv3 ...
#define TOD_POWER_SLOT_LV2        6        // ... and another at Lv6
#define TOD_POWER_MANGLER_LV      9        // a second Mangler at Lv9
#define TOD_POWER_LIFE_STEP       0.81     // helpers last longer on the LOG curve: x1.24 at Lv1 ... x1.81 at Lv9 (user 2026-09-28: "more health at each level")
#define TOD_POWER_ELITE_STEP      1.98     // helper hits on elites on the LOG curve: x1.60 at Lv1 ... x2.98 at Lv9 (user 2026-09-28: "more damage at each level")
#define TOD_POWER_THRALL_KILLS    2        // +2 thrall kills / Lv (12 -> 30)
#define TOD_POWER_BIND_STEP       0.071    // bind time x(1 - 0.071 Lv): 7.2 s -> 2.6 s at Lv9 (user: "the upgrade is that it takes less and less time")
// SOUL BEAM (id 39, "soulbeam", max 9) - the Necromancer's CORE WEAPON card (2026-09-27).
// The user: the beam "kills things instantly, which I don't think it should" and "an
// extra soul" at each step. Per level: beam damage on the log curve (card_curve), -5% beam cost. At Lv3 / Lv6 /
// Lv9: one more soul at once, and the soul-rip comes 0.15 s sooner (_tod_necro_skull
// TOD_NECRO_SOUL_MIN_MS). LOCKSTEP tod_upgrade.lua DETAIL[39].
#define TOD_CARD_BEAM_MAX         9
#define TOD_BEAM_DMG_STEP         0.90     // beam damage on the LOG curve: x1.27 at Lv1 ... x1.90 at Lv9 (user 2026-09-28) - replaces the DAMAGE card for the skull
#define TOD_BEAM_COST_STEP        0.05     // beam meter cost -5% / Lv (-45% at Lv9)
#define TOD_BEAM_RIP_STEP_MS      150      // soul-rip minimum -150 ms per bucket
// THE BUILD CARDS (2026-09-27, _tod_class_cards header). LOCKSTEP tod_upgrade.lua DETAIL 5 / 10 / 19.
// REAPER'S REACH (id 5, "reaperreach", weapon lane): beam reach +4% / Lv (500 -> 680, packed 650 -> 884);
// the acquire cone widens at Lv3 / Lv6 / Lv9 (dot 0.85 -> 0.82 / 0.79 / 0.76).
#define TOD_REACH_RANGE_STEP      0.04
#define TOD_REACH_DOT_STEP        0.03
// PACK MASTER (id 10, "packmaster", kit lane): helper hits on elites +10% / Lv; Lv3 hound bites every
// 0.5 s (0.7), Lv6 the Mangler's cannon every 2.5 s (4), Lv9 a thrall that falls tears out the souls
// of ordinary zombies within 150.
#define TOD_PACK_ELITE_STEP       0.10
#define TOD_PACK_BITE_MS          500
#define TOD_PACK_CANNON_MS        2500
#define TOD_PACK_BURST_R          150
// BURNED OUT (id 19, "burnedout", kit lane): every Widow's Wine burst refills 2 soul meter / Lv; one
// more burst charge at Lv3 / Lv6 / Lv9 (4 -> 7).
#define TOD_BURNCARD_METER_LV     2

function init()
{
	callback::on_spawned( &on_spawned );
	dev_log( "INIT rev=12 models=black pay_first=1 no_melee=1 rate_tick=1 variant0=1 lift=one_play_hold hold_rate=" + TOD_BIND_HOLD_RATE + " aura=no_flames pulse=wave_only blink_s=" + TOD_HELPER_BLINK_S + " bind_ms=" + TOD_BIND_MS + " lift_ms=" + TOD_BIND_LIFT_MS + " thrall=" + TOD_THRALL_MAX + "x" + TOD_THRALL_COST + " hound=" + TOD_HOUND_MAX + "x" + TOD_HOUND_COST
		+ " mangler=" + TOD_MANGLER_MAX + "x" + TOD_MANGLER_COST + " bomb_r=" + TOD_BOMB_RADIUS + " bomb_pct=" + TOD_BOMB_ROUND_PCT + " bomb_min=" + TOD_BOMB_SOULS_MIN
		+ " spawners=" + ( isdefined( level.zombie_spawners ) ? level.zombie_spawners.size : -1 ) );
}

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_NECRO_SUMMON] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// =============================================================================
// per life
// =============================================================================
function on_spawned()
{
	self.tod_necro_pulse_busy = false;
	self.tod_necro_pulse_token = undefined;
	self notify( "tod_necro_summon_respawn" );
	self dismiss_all( "respawn" );
	self bind_cancel( "respawn" );
	self.tod_summon_next = 0;
	self.tod_bind_pick_next = 0;
	self.tod_summon_deny_ms = 0;
	if ( !isdefined( self.tod_bomb_souls ) ) self.tod_bomb_souls = 0;   // the charge survives a death; it starts empty
	self thread owner_watch();
}

function is_necro()
{
	return ( isdefined( self.tod_class ) && self.tod_class == TOD_NECRO_CLASS );
}

function tier()
{
	if ( !isdefined( self.tod_tier ) ) return 1;
	return self.tod_tier;
}

// helpers go when you go down, die, leave or stop being a Necromancer
function owner_watch()
{
	self endon( "disconnect" );
	self endon( "tod_necro_summon_respawn" );
	for ( ;; )
	{
		wait 0.25;
		if ( isdefined( self.tod_necro_bind_t0 ) && ( !IsAlive( self ) || self laststand::player_is_in_laststand() ) )
			self bind_cancel( "owner_down" );
		if ( !isdefined( self.tod_necro_helpers ) || self.tod_necro_helpers.size == 0 ) continue;
		why = undefined;
		if ( !IsAlive( self ) ) why = "owner_dead";
		else if ( self laststand::player_is_in_laststand() ) why = "owner_down";
		else if ( !self is_necro() ) why = "class_change";
		if ( isdefined( why ) ) self dismiss_all( why );
	}
}

function helpers()
{
	if ( !isdefined( self.tod_necro_helpers ) ) self.tod_necro_helpers = [];
	live = [];
	foreach ( h in self.tod_necro_helpers )
		if ( isdefined( h ) && IsAlive( h ) ) live[ live.size ] = h;
	self.tod_necro_helpers = live;
	return live;
}

function count_kind( kind )
{
	n = 0;
	foreach ( h in self helpers() )
		if ( h.tod_necro_kind == kind ) n++;
	return n;
}

// for the HUD: helpers alive
function helpers_alive()
{
	return self helpers().size;
}

function dismiss_all( why )
{
	foreach ( h in self helpers() )
		h thread helper_end( why );
}

// =============================================================================
// AIM = BIND A ZOMBIE. Called by _tod_necro_skull every tick while the skull is
// held. Returns true while the torch light should show.
// =============================================================================
function aim_tick( aim )
{
	if ( !aim )
	{
		self.tod_summon_denied = undefined;   // PK18: the next refused aim is heard again
		self bind_cancel( "released" );
		return false;
	}
	now = GetTime();
	b = self.tod_necro_bind;
	if ( isdefined( self.tod_necro_bind_t0 ) )
	{
		if ( !self bind_holds( b ) ) { self bind_cancel( "lost_" + self bind_lost_why( b ) ); return true; }
		held = now - self.tod_necro_bind_t0;
		if ( !IS_TRUE( self.tod_necro_bind_lifted ) ) self bind_lift( b );   // (bind_start lifts it; this only covers a missed start)
		if ( held >= self.tod_necro_bind_ms ) self bind_finish( b );
		return true;
	}
	if ( now < self.tod_summon_next ) return true;
	kind = self next_kind();
	if ( !isdefined( kind ) ) return self deny( "slots" );
	cost = kind_cost( kind );
	if ( self.tod_necro_meter < cost ) return self deny( "meter need=" + cost + " have=" + Int( self.tod_necro_meter ) );
	// a thrall IS the bound zombie; a hound / Mangler is a new actor
	if ( kind != "thrall" && GetFreeActorCount() < TOD_SUMMON_ACTOR_RESERVE ) return self deny( "actor_budget free=" + GetFreeActorCount() );
	if ( now < self.tod_bind_pick_next ) return true;
	self.tod_bind_pick_next = now + 150;
	z = self bind_pick();
	if ( isdefined( z ) ) self bind_start( z, kind );
	else if ( GetTime() >= self.tod_summon_deny_ms )
	{
		self.tod_summon_deny_ms = GetTime() + 1500;
		dev_log( "BIND_SEARCH player=" + self GetEntityNumber() + " none_on_crosshair kind=" + kind + " tier=" + self tier() + " reach=" + TOD_SUMMON_REACH + " dot=" + TOD_BIND_DOT );
	}
	return true;   // no zombie on the crosshair: the torch still shows, searching
}

// the ordinary zombie nearest the crosshair, in reach and in sight
function bind_pick()
{
	eye = self GetEye();
	fwd = AnglesToForward( self GetPlayerAngles() );
	best = undefined;
	bd = TOD_BIND_DOT;
	foreach ( z in GetAITeamArray( level.zombie_team ) )
	{
		if ( !isdefined( z ) || !IsAlive( z ) || IS_TRUE( z.marked_for_death ) || isdefined( z.tod_necro_binder ) ) continue;
		if ( is_elite( z ) || !IS_TRUE( z.completed_emerging_into_playable_area ) ) continue;
		c = z GetCentroid();
		if ( DistanceSquared( eye, c ) > TOD_SUMMON_REACH * TOD_SUMMON_REACH ) continue;
		d = VectorDot( VectorNormalize( c - eye ), fwd );
		if ( d < bd ) continue;
		if ( !SightTracePassed( eye, c, false, self ) ) continue;
		best = z;
		bd = d;
	}
	return best;
}

function bind_holds( z )
{
	if ( !isdefined( z ) || !IsAlive( z ) || z.tod_necro_binder !== self ) return false;
	if ( GetTime() - self.tod_necro_bind_t0 > TOD_BIND_MAX_MS ) return false;
	if ( DistanceSquared( self.origin, z.origin ) > TOD_SUMMON_REACH * TOD_SUMMON_REACH * 1.3225 ) return false;   // x1.15 reach
	return ( self util::is_player_looking_at( z GetCentroid(), TOD_BIND_HOLD_DOT, false ) || self util::is_player_looking_at( z.origin, TOD_BIND_HOLD_DOT, false ) );
}

// which bind_holds rule let go - the cancel log names it (2026-10-05: the user's run lost
// most binds 5.5-6.9 s into 7.2 and the log could not say whether it was the aim, the
// distance or a teammate's kill)
function bind_lost_why( z )
{
	if ( !isdefined( z ) || !IsAlive( z ) ) return "dead";
	if ( z.tod_necro_binder !== self ) return "taken";
	if ( GetTime() - self.tod_necro_bind_t0 > TOD_BIND_MAX_MS ) return "timeout";
	if ( DistanceSquared( self.origin, z.origin ) > TOD_SUMMON_REACH * TOD_SUMMON_REACH * 1.3225 ) return "far";
	return "aim";
}

// how long this Necromancer's bind takes (SUMMONING POWER)
function bind_ms()
{
	return Int( TOD_BIND_MS * ( 1 - TOD_POWER_BIND_STEP * self power_lv() ) );
}

// the bind starts: the souls flow in (state 3), the skull breathes and the zombie
// is lifted at once for the whole bind (bind_lift)
function bind_start( z, kind )
{
	self.tod_necro_bind = z;
	self.tod_necro_bind_kind = kind;
	self.tod_necro_bind_t0 = GetTime();
	self.tod_necro_bind_ms = self bind_ms();   // latched: a card mid-bind does not move the finish line
	self.tod_necro_bind_lifted = false;
	z.tod_necro_binder = self;
	// OFF LIMITS WHILE BOUND (2026-10-05, the 17:33 run): the player's own thrall or companion could pick the
	// lifted zombie and kill it, and the bind ended "lost". AI leave it alone for the bind (ignoreme, the
	// zombie's own value kept and put back by bind_drop / bind_finish); helper_target and the companions'
	// target_for skip tod_necro_binder as well.
	z.tod_necro_bind_ig = ( IS_TRUE( z.ignoreme ) ? 1 : 0 );
	z.ignoreme = true;
	// THE SHIELD (LT-fix 2026-10-05): ignoreme alone does not stop a THRALL. A turned zombie picks its prey with
	// stock findZombieEnemy (_zm_behavior.gsc: it never reads ignoreme, and stock zombieFindFlesh writes the
	// zombie's ignoreme back to false every think) and Kill()s it on its swing (zombie.gsc zombieNotetrackMeleeFire).
	// Both skip a zombie whose allowDeath is false (is_magic_bullet_shield_enabled), so the lifted zombie cannot die
	// for the bind's length; bind_drop / bind_finish hand the old value back (bind_unshield). The 17:33 run lost 5 of
	// 15 binds this way (BIND_CANCEL lost alive=0, the thrall's HELPER_KILL 0-200 ms before each). Teammates' shots
	// wound it but cannot finish it while it is bound; soul_kill spares it too (the hounds, the Mangler, the bomb).
	z.tod_necro_bind_allowdeath = z.allowDeath;
	z.tod_necro_shielded = true;
	z.allowDeath = false;
	z clientfield::set( "tod_necro_soul", TOD_SOUL_BIND );
	z thread zombie_utility::zombie_eye_glow_stop();
	z PlaySound( "evt_zombie_skull_breathe" );
	z thread bind_guard( self );
	self bind_lift( z );
	dev_log( "BIND player=" + self GetEntityNumber() + " target=" + z GetEntityNumber() + " kind=" + kind + " tier=" + self tier() + " shield=1"
		+ " ms=" + self.tod_necro_bind_ms + " power_lv=" + self power_lv()
		+ " dist=" + Int( Distance( self.origin, z.origin ) ) + " meter=" + Int( self.tod_necro_meter ) );
}

// Rise into the death-ray's suspended pose, then hold that exact pose until the
// bind ends. Stock _blend_out compares CLIP time to .3, ignoring the slowed rate;
// stretching the whole clip therefore released AI up to 1.44 s before conversion.
function bind_lift( z )
{
	self.tod_necro_bind_lifted = true;
	if ( !isdefined( z ) || !IsAlive( z ) ) return;
	if ( z IsPlayingAnimScripted() ) z StopAnimScripted( 0.3 );
	z.tod_necro_lifted = true;   // bind_drop / bind_finish stop the anim only if it started
	z.tod_necro_bind_origin = z.origin;
	z.tod_necro_bind_angles = z.angles;
	z thread bind_pose( self );
	dev_log( "BIND_LIFT player=" + self GetEntityNumber() + " target=" + z GetEntityNumber()
		+ " at_ms=" + ( GetTime() - self.tod_necro_bind_t0 ) + " of_ms=" + self.tod_necro_bind_ms + " pose_hold=1" );
}

function bind_pose( owner ) // self = zombie; cancellation also cancels the delayed hold
{
	self endon( "death" );
	self endon( "tod_necro_bind_end" );
	// Never enter the last (fall/release) portion of this non-looping death clip.
	pose = 0.55;
	rise_s = min( 1.0, owner.tod_necro_bind_ms / 2000 );
	rate = GetAnimLength( TOD_BIND_ANIM ) * pose / rise_s;
	// ONE PLAY, NEVER RESTARTED (user 2026-10-05: "they go up and animate, and then they
	// stick to the floor and then freeze while you're still summoning them"). The hold
	// used to be a SECOND play of the clip at its 55% pose, and a play starts the zombie
	// at the align point - the floor - so the lifted body dropped and froze there for
	// the rest of the bind. Now the clip plays once and bind_hold_keep slows it where it
	// is. The rise's pace rides the ASM rate with the clip at 1, so it is exact whether
	// the engine multiplies the two rates or the ASM rate wins (the hold works the same way).
	self ASMSetAnimationRate( rate );
	self thread animation::play( TOD_BIND_ANIM, self.tod_necro_bind_origin, self.tod_necro_bind_angles, 1, 0.2, 0 );
	wait rise_s;
	if ( !isdefined( owner ) || self.tod_necro_binder !== owner ) return;
	self thread bind_hold_keep( owner );
	dev_log( "BIND_HOLD target=" + self GetEntityNumber() + " pose=" + pose + " hold_rate=" + TOD_BIND_HOLD_RATE
		+ " lift_z=" + Int( self.origin[ 2 ] - self.tod_necro_bind_origin[ 2 ] ) + " held_ms=" + ( GetTime() - owner.tod_necro_bind_t0 ) + " until_ms=" + owner.tod_necro_bind_ms );
}

// THE HOLD: the lift's own clip keeps running where it is, slowed to TOD_BIND_HOLD_RATE,
// so the zombie stays up in the souls until the bind ends. Every frame, because the
// round's pace sweep, the world pause and its release all write this same rate.
function bind_hold_keep( owner )   // self = the zombie
{
	self endon( "death" );
	self endon( "tod_necro_bind_end" );
	while ( IS_TRUE( self.tod_necro_lifted ) && self.tod_necro_binder === owner )
	{
		self ASMSetAnimationRate( TOD_BIND_HOLD_RATE );
		wait 0.05;
	}
}

// the owner vanishes mid-bind (disconnect): the zombie is let go, never left hanging
function bind_guard( owner )   // self = the zombie
{
	self endon( "death" );
	for ( ;; )
	{
		wait 0.25;
		if ( self.tod_necro_binder !== owner ) return;
		if ( !isdefined( owner ) )
		{
			self bind_drop();
			dev_log( "BIND_CANCEL target=" + self GetEntityNumber() + " why=owner_gone" );
			return;
		}
	}
}

// hands back the allowDeath bind_start took (LT-fix 2026-10-05); returns the value it restored, or -1 when the zombie
// was not shielded. self = the zombie.
function bind_unshield()
{
	if ( !IS_TRUE( self.tod_necro_shielded ) ) return -1;
	was = self.tod_necro_bind_allowdeath;
	if ( !isdefined( was ) ) was = true;
	self.allowDeath = was;
	self.tod_necro_shielded = undefined;
	self.tod_necro_bind_allowdeath = undefined;
	return was;
}

// back into the horde as it was
function bind_drop()   // self = the zombie
{
	self notify( "tod_necro_bind_end" );
	self.tod_necro_binder = undefined;
	if ( isdefined( self.tod_necro_bind_ig ) ) { self.ignoreme = ( self.tod_necro_bind_ig == 1 ); self.tod_necro_bind_ig = undefined; }   // bind_start's snapshot
	self bind_unshield();   // the shield off (LT-fix): a live zombie can die again
	if ( !IsAlive( self ) )
	{
		self clientfield::set( "tod_necro_soul", 0 );
		return;
	}
	if ( IS_TRUE( self.tod_necro_lifted ) )
	{
		self animation::stop( 0.3 );   // back to its own feet
		self ASMSetAnimationRate( 1 );   // the hold's crawl off; the pace sweep puts the round's rate back within 1.5 s
	}
	self.tod_necro_lifted = undefined;
	self thread zombie_utility::zombie_eye_glow();
	self clientfield::set( "tod_necro_soul", 0 );
}

function bind_cancel( why )
{
	if ( !isdefined( self ) || !isdefined( self.tod_necro_bind_t0 ) ) return;
	z = self.tod_necro_bind;
	held = GetTime() - self.tod_necro_bind_t0;
	self.tod_necro_bind = undefined;
	self.tod_necro_bind_t0 = undefined;
	if ( isdefined( z ) && z.tod_necro_binder === self ) z bind_drop();
	dev_log( "BIND_CANCEL player=" + self GetEntityNumber() + " why=" + why + " held_ms=" + held
		+ " target=" + ( isdefined( z ) ? z GetEntityNumber() : -1 ) + " alive=" + ( isdefined( z ) && IsAlive( z ) ) );
}

// the bind completes: tier 1 turns that zombie, tiers 2/3 raise a helper from its body
function bind_finish( z )
{
	kind = self next_kind();   // slots / meter may have moved during the lift
	if ( !isdefined( kind ) || self.tod_necro_meter < kind_cost( kind ) )
	{
		self bind_cancel( ( isdefined( kind ) ? "meter" : "slots" ) );
		return;
	}
	held = GetTime() - self.tod_necro_bind_t0;
	dev_log( "BIND_CONVERT target=" + z GetEntityNumber() + " held_ms=" + held + " scripted=" + z IsPlayingAnimScripted()
		+ " lift_z=" + ( isdefined( z.tod_necro_bind_origin ) ? Int( z.origin[ 2 ] - z.tod_necro_bind_origin[ 2 ] ) : -1 ) );
	self.tod_necro_bind = undefined;
	self.tod_necro_bind_t0 = undefined;
	self.tod_summon_next = GetTime() + TOD_SUMMON_REPEAT_MS;
	z notify( "tod_necro_bind_end" );
	z.tod_necro_binder = undefined;
	// the shield off BEFORE soul_kill (LT-fix): its DoDamage( health + 666 ) needs a zombie that can die; a thrall's
	// thrall_make sets allowDeath false again in this same frame
	z bind_unshield();
	// Body replacements stay suspended through soul_kill_run's replication frame.
	if ( kind == "thrall" && IS_TRUE( z.tod_necro_lifted ) ) z animation::stop( 0 );
	if ( isdefined( z.tod_necro_bind_ig ) ) { z.ignoreme = ( z.tod_necro_bind_ig == 1 ); z.tod_necro_bind_ig = undefined; }   // bind_start's snapshot (a thrall then sets its own)
	if ( IS_TRUE( z.tod_necro_lifted ) ) z ASMSetAnimationRate( 1 );   // the hold's crawl off before it walks (thrall) or dies (body): a death at the hold rate would play 100x slow
	z.tod_necro_lifted = undefined;
	h = undefined;
	how = "turned";
	if ( kind == "thrall" )
	{
		self thrall_make( z );
		h = z;
	}
	else
	{
		how = "body";
		pos = GetClosestPointOnNavMesh( z.origin, 96 );
		if ( !isdefined( pos ) ) pos = self summon_point();
		soul_kill( z, self, undefined, "bind", 0 );   // its soul is torn out; the helper rises from it
		if ( isdefined( pos ) ) h = self summon( kind, pos );
	}
	if ( !isdefined( h ) )
	{
		self deny( "spawn_failed kind=" + kind );
		return;
	}
	if ( kind == "thrall" ) self helper_register( h, kind );
	cost = kind_cost( kind );
	self.tod_necro_meter -= cost;
	self.tod_necro_last_use = GetTime();
	dev_log( "SUMMON player=" + self GetEntityNumber() + " kind=" + kind + " how=" + how + " tier=" + self tier() + " held_ms=" + held
		+ " meter=" + Int( self.tod_necro_meter ) + " alive=" + self helpers().size + " max=" + self helper_max( kind )
		+ " power_lv=" + self power_lv() + " life_s=" + self kind_life( kind ) + " ent=" + h GetEntityNumber() );
}

function deny( why )
{
	// PK18: a refused bind is HEARD - once per aim (aim_tick re-arms it on release), never a nope every 1.5 s
	// while a player holds the aim on an empty meter
	if ( !IS_TRUE( self.tod_summon_denied ) )
	{
		self.tod_summon_denied = true;
		tod_ability_fx::kit_deny( self, "summon", why );
	}
	if ( GetTime() >= self.tod_summon_deny_ms )
	{
		self.tod_summon_deny_ms = GetTime() + 1500;
		dev_log( "DENY player=" + self GetEntityNumber() + " why=" + why + " tier=" + self tier() );
	}
	return false;
}

function next_kind()
{
	t = self tier();
	if ( t >= 3 )
	{
		if ( self count_kind( "mangler" ) < self helper_max( "mangler" ) ) return "mangler";
		if ( self count_kind( "hound" ) < self helper_max( "hound" ) ) return "hound";
		return undefined;
	}
	if ( t == 2 )
	{
		if ( self count_kind( "hound" ) < self helper_max( "hound" ) ) return "hound";
		return undefined;
	}
	if ( self count_kind( "thrall" ) < self helper_max( "thrall" ) ) return "thrall";
	return undefined;
}

// =============================================================================
// THE CLASS CARDS (self = the Necromancer)
// =============================================================================
function card_lv( key, cap )
{
	if ( !isdefined( self ) || !isdefined( self.tod_levels ) || !isdefined( self.tod_levels[ key ] ) ) return 0;
	lv = Int( self.tod_levels[ key ] );
	if ( lv < 0 ) return 0;
	if ( lv > cap ) return cap;
	return lv;
}

// THE DAMAGE CURVE (user 2026-09-28: damage "should just increase logarithmically",
// no 3/6/9 jump; only counts - souls at once, slots, radius - step at 3/6/9):
// ln( 1 + lvl ) / ln( 10 ) as a table (no log native) - 0 at Lv0, 1 at Lv9, and every
// level adds (Lv1 30% of the way, Lv5 78%). Same formula as tod_archer::grapple_curve.
// LOCKSTEP tod_upgrade.lua CARD_CURVE.
function card_curve( lvl )
{
	if ( !isdefined( lvl ) || lvl <= 0 ) return 0;
	if ( lvl >= 9 ) return 1;
	c = array( 0, 0.301, 0.4771, 0.6021, 0.699, 0.7782, 0.8451, 0.9031, 0.9542, 1 );
	return c[ lvl ];
}

function bomb_lv()  { return self card_lv( "soulbomb", TOD_CARD_BOMB_MAX ); }
function power_lv() { return self card_lv( "summonpower", TOD_CARD_POWER_MAX ); }
function beam_lv()  { return self card_lv( "soulbeam", TOD_CARD_BEAM_MAX ); }

// the souls to charge the Soul Bomb: a share of THIS round's zombies. The round
// total is stock's own count for the round and party size (_tod_luck publishes
// level.tod_round_zombie_total each round: zm::get_zombie_count_for_round, which
// already grows with co-op), so it scales with both.
// Solo r1 3, r10 17, r20 30; four players r20 120. Logged when it changes.
function bomb_souls_need()
{
	total = level.tod_round_zombie_total;
	if ( !isdefined( total ) || total < 1 ) total = TOD_BOMB_ROUND_FALLBACK;
	// the card takes TOD_BOMB_PCT_STEP of the round off per level, but never less than
	// ONE SOUL per level (Archer audit 2026-09-28: on a 20-zombie round the share cut
	// rounded to nothing, so a SUPER bought no charge). Floor TOD_BOMB_SOULS_MIN.
	lv = self bomb_lv();
	pct = TOD_BOMB_ROUND_PCT - TOD_BOMB_PCT_STEP * lv;
	base = Int( total * TOD_BOMB_ROUND_PCT + 0.999 );
	cut = base - Int( total * pct + 0.999 );
	if ( cut < lv ) cut = lv;
	need = base - cut;
	if ( need < TOD_BOMB_SOULS_MIN ) need = TOD_BOMB_SOULS_MIN;
	if ( self.tod_bomb_need_last !== need )
	{
		self.tod_bomb_need_last = need;
		dev_log( "BOMB_NEED player=" + self GetEntityNumber() + " round=" + ( isdefined( level.round_number ) ? level.round_number : -1 ) + " total=" + total
			+ " pct=" + pct + " need=" + need + " have=" + ( isdefined( self.tod_bomb_souls ) ? self.tod_bomb_souls : 0 ) + " party=" + GetPlayers().size + " lv=" + self bomb_lv() );
	}
	return need;
}
function bomb_radius()        { return TOD_BOMB_RADIUS + TOD_BOMB_RADIUS_STEP * Int( self bomb_lv() / 3 ); }   // buckets: Lv3 / Lv6 / Lv9
function bomb_elite_zombies() { return TOD_BOMB_ELITE + TOD_BOMB_ELITE_STEP * card_curve( self bomb_lv() ); }

function power_slots()
{
	lv = self power_lv();
	n = 0;
	if ( lv >= TOD_POWER_SLOT_LV1 ) n++;
	if ( lv >= TOD_POWER_SLOT_LV2 ) n++;
	return n;
}

function helper_max( kind )
{
	if ( kind == "mangler" ) return TOD_MANGLER_MAX + ( self power_lv() >= TOD_POWER_MANGLER_LV ? 1 : 0 );
	if ( kind == "hound" ) return ( self tier() >= 3 ? TOD_HOUND_MAX_T3 : TOD_HOUND_MAX ) + self power_slots();
	return TOD_THRALL_MAX + self power_slots();
}

function helper_life_mult()  { return 1 + TOD_POWER_LIFE_STEP * card_curve( self power_lv() ); }
function helper_elite_mult() { return ( 1 + TOD_POWER_ELITE_STEP * card_curve( self power_lv() ) ) * ( 1 + TOD_PACK_ELITE_STEP * self pack_lv() ); }   // x PACK MASTER (2026-09-27)
function thrall_kill_limit() { return TOD_THRALL_KILLS + TOD_POWER_THRALL_KILLS * self power_lv(); }

// the skull's beam (_tod_necro_skull.gsc) reads these (SOUL BEAM, the core card)
function beam_bucket()     { lv = self beam_lv(); b = Int( lv / 3 ); if ( b > 3 ) b = 3; return b; }
function beam_targets_add() { return self beam_bucket(); }   // +1 soul at once at Lv3 / Lv6 / Lv9
function beam_dmg_mult()   { return 1 + TOD_BEAM_DMG_STEP * card_curve( self beam_lv() ); }
function beam_cost_mult()  { return 1 - TOD_BEAM_COST_STEP * self beam_lv(); }
function beam_rip_cut_ms() { return TOD_BEAM_RIP_STEP_MS * self beam_bucket(); }

// THE BUILD CARDS (self = the Necromancer)
function card_bucket( key )   { l = self card_lv( key, 9 ); b = Int( l / 3 ); if ( b > 3 ) b = 3; return b; }
function reach_range_mult()   { return 1 + TOD_REACH_RANGE_STEP * self card_lv( "reaperreach", 9 ); }
function reach_dot_cut()      { return TOD_REACH_DOT_STEP * self card_bucket( "reaperreach" ); }
function pack_lv()            { return self card_lv( "packmaster", 9 ); }
function pack_bite_ms()       { return ( ( self pack_lv() >= 3 ) ? TOD_PACK_BITE_MS : TOD_HOUND_BITE_MS ); }
function pack_cannon_ms()     { return ( ( self pack_lv() >= 6 ) ? TOD_PACK_CANNON_MS : TOD_MANGLER_CANNON_MS ); }
function burn_card_bonus()    { return self card_bucket( "burnedout" ); }   // extra Burned Out charges
function burn_card_meter()    { return TOD_BURNCARD_METER_LV * self card_lv( "burnedout", 9 ); }

function kind_cost( kind )
{
	if ( kind == "mangler" ) return TOD_MANGLER_COST;
	if ( kind == "hound" ) return TOD_HOUND_COST;
	return TOD_THRALL_COST;
}

function kind_life( kind )
{
	if ( kind == "mangler" ) life = TOD_MANGLER_LIFE;
	else if ( kind == "hound" ) life = TOD_HOUND_LIFE;
	else life = TOD_THRALL_LIFE;
	return life * self helper_life_mult();   // SUMMONING POWER
}

// where you are looking, dropped to the floor and snapped to the navmesh
function summon_point()
{
	eye = self GetEye();
	dir = AnglesToForward( self GetPlayerAngles() );
	tr = BulletTrace( eye, eye + dir * TOD_SUMMON_REACH, false, self );
	p = tr[ "position" ] - dir * 32;
	down = BulletTrace( p + ( 0, 0, 16 ), p - ( 0, 0, 600 ), false, self );
	nav = GetClosestPointOnNavMesh( down[ "position" ], 96 );
	if ( !isdefined( nav ) || abs( nav[ 2 ] - self.origin[ 2 ] ) > 200 )
		nav = GetClosestPointOnNavMesh( self.origin + dir * 72, 96 );
	if ( !isdefined( nav ) || abs( nav[ 2 ] - self.origin[ 2 ] ) > 200 ) return undefined;
	return nav;
}

function summon( kind, pos )
{
	tod_perk_scatter::play_sound_at_origin( pos, "evt_zombie_skull_breathe", 3 );
	h = undefined;
	if ( kind == "hound" ) h = self spawn_hound( pos );
	else if ( kind == "mangler" ) h = self spawn_mangler( pos );
	if ( !isdefined( h ) ) return undefined;
	self helper_register( h, kind );
	return h;
}

function helper_register( h, kind )
{
	h.tod_necro_helper = true;
	h.tod_necro_owner = self;
	h.tod_necro_kind = kind;
	h.tod_necro_kills = 0;
	h.tod_hpbar_frac = 1;   // THE WHITE BAR (_tod_elite_hp): full on the frame it becomes a helper
	self helpers();
	self.tod_necro_helpers[ self.tod_necro_helpers.size ] = h;
	h thread helper_life( self, self kind_life( kind ) );
}

// =============================================================================
// THRALLS
// =============================================================================
// stock Turned's result() on a live zombie, field for field, plus the map's
// exemptions (self = the Necromancer, guy = the bound zombie)
function thrall_make( guy )
{
	guy.team = "allies";
	guy.aat_turned = true;
	guy.n_aat_turned_zombie_kills = 0;
	guy.allowDeath = false;
	guy.allowpain = false;
	guy.no_gib = true;
	guy.no_powerups = true;
	guy.ignore_enemy_count = true;
	guy.ignore_nuke = true;
	guy.ignore_round_spawn_failsafe = true;
	guy.disableAmmoDrop = true;
	guy.deathpoints_already_given = true;
	guy.no_damage_points = true;
	guy.ignoreme = true;
	guy.favoriteenemy = undefined;
	guy zombie_utility::set_zombie_run_cycle( "sprint" );
	guy thrall_look();   // the black body + the black white-eyed head (the charcoal eyes are baked red in the material)
	guy clientfield::set( "tod_necro_soul", TOD_SOUL_THRALL );   // the thrall aura + a white eye glow (the arrival burst plays on the 3 -> 5 edge)
	guy SetPlayerCollision( false );
	tod_perk_scatter::play_sound_at_origin( guy.origin, "evt_zombie_skull_breathe", 3 );
}

// the thrall's own look (self = the zombie being turned): the black body and the black,
// white-eyed head. The head (and hat) come off BEFORE SetModel, so what is attached
// afterwards is exactly what this puts back, whatever SetModel does to attachments;
// both stock gib-data layouts kept in step (_tod_cyber_zombies' sprinter head swap).
function thrall_look()
{
	ent = self GetEntityNumber();
	body_old = self.model;
	head_old = GIB_HEAD_MODEL( self );
	has_head = ( !IS_TRUE( self.head_gibbed ) && isdefined( head_old ) && head_old != "" );
	hat = GIB_HAT_MODEL( self );
	if ( has_head )
	{
		if ( isdefined( hat ) && hat != "" ) self Detach( hat, "" );
		self Detach( head_old, "" );
	}
	body_new = body_old;
	if ( body_old === TOD_THRALL_BODY_DONOR )
	{
		self SetModel( TOD_THRALL_BODY );
		body_new = TOD_THRALL_BODY;
	}
	head_new = "none";
	if ( has_head )
	{
		head_new = ( head_old == TOD_THRALL_HEAD_DONOR ? TOD_THRALL_HEAD : head_old );
		self Attach( head_new, "" );
		self.head = head_new;
		self.hatmodel = undefined;
		if ( isdefined( self.gib_data ) )
		{
			self.gib_data.head = head_new;
			self.gib_data.hatmodel = undefined;
		}
	}
	dev_log( "THRALL_LOOK ent=" + ent + " body=" + ( isdefined( body_old ) ? body_old : "none" ) + "->" + body_new
		+ " head=" + ( isdefined( head_old ) ? head_old : "none" ) + "->" + head_new + " hat=" + ( isdefined( hat ) && hat != "" ? hat : "none" )
		+ " black_body=" + ( body_new === TOD_THRALL_BODY ) + " black_head=" + ( head_new == TOD_THRALL_HEAD ) );
}

// stock Turned counts its own kills (zombie.gsc); pay the owner for each one
function thrall_kill_pay( owner )
{
	n = ( isdefined( self.n_aat_turned_zombie_kills ) ? self.n_aat_turned_zombie_kills : 0 );
	while ( self.tod_necro_kills < n )
	{
		self.tod_necro_kills++;
		pay_kill( owner, self, "thrall_swing" );
	}
	return ( n >= owner thrall_kill_limit() );   // SUMMONING POWER: +2 / Lv
}

// =============================================================================
// SOUL HOUNDS
// =============================================================================
function spawn_hound( pos )
{
	level.dog_health = 3000;   // TRAP 1 (map 1 / the retired _tod_hellhounds): read by dog_init at spawn
	// TRAP 2, moved here from the retired _tod_hellhounds (2026-10-05): stock defaults
	// this to 4.0 and dog_init multiplies by it; pinned so the soul hound's health is
	// the number above. Set beside level.dog_health, right before every spawn.
	SetDvar( "scr_dog_health_walk_multiplier", "1.0" );
	yaw = self.angles[ 1 ];
	dog = SpawnActor( "spawner_zm_factory_zombie_dog", pos, ( 0, yaw, 0 ), "tod_necro_hound", true );
	if ( !isdefined( dog ) ) return undefined;
	dog SetModel( TOD_HOUND_MODEL );   // black, white eyes - never the enemy hellhound's look
	dev_log( "HELPER_MODEL ent=" + dog GetEntityNumber() + " kind=hound model=" + dog.model );
	// SAME FRAME (_tod_hellhounds TRAP 3): keep _tod_zombie_speed off it. No
	// is_boss / tod_boss_kind: it is not an elite (no RED bar, no elite roof); its
	// WHITE helper bar comes from tod_necro_helper (helper_register, _tod_elite_hp).
	dog.tod_boss_custom_speed = true;
	dog.team = "allies";
	dog.health = 3000;
	dog.maxhealth = 3000;
	dog.ignore_enemy_count = true;
	dog.ignore_round_spawn_failsafe = true;
	dog.ignore_nuke = true;
	dog.no_powerups = true;
	dog.disableAmmoDrop = true;
	dog.allow_zombie_to_target_ai = 0;
	dog.ignoreme = true;
	dog thread hound_think( self );
	return dog;
}

function hound_think( owner )
{
	self endon( "death" );
	wait 0.3;
	self clientfield::set( "tod_necro_soul", TOD_SOUL_HOUND );   // the soul body, never dog_fx's fire
	self SetPlayerCollision( false );
	next_bite = 0;
	for ( ;; )
	{
		wait 0.1;
		if ( !isdefined( owner ) ) return;
		if ( IS_TRUE( self.tod_necro_paused ) ) continue;
		t = helper_target( self, owner );
		if ( !isdefined( t ) )
		{
			self.favoriteenemy = undefined;
			self helper_follow( owner );
			continue;
		}
		self.favoriteenemy = t;
		self helper_goal( t.origin, "target", t );
		if ( GetTime() >= next_bite && DistanceSquared( self.origin, t.origin ) < TOD_HOUND_BITE_RANGE * TOD_HOUND_BITE_RANGE )
		{
			next_bite = GetTime() + owner pack_bite_ms();   // PACK MASTER Lv3: 0.5 s
			tod_perk_scatter::play_sound_at_origin( self.origin, "hb_bo6_fly_ai_ghoul_melee", 2 );   // the bite (hb_bo6_ghoul.csv)
			if ( is_elite( t ) ) helper_hurt( t, round_zombie() * TOD_HOUND_ELITE_BITE * owner helper_elite_mult(), owner );
			else soul_kill( t, owner, self, "hound_bite", 0 );
		}
	}
}

// =============================================================================
// THE MANGLER
// =============================================================================
function spawn_mangler( pos )
{
	actor = SpawnActor( "spawner_hb_mangler", pos, ( 0, self.angles[ 1 ], 0 ), "tod_necro_mangler", true );
	if ( !isdefined( actor ) ) return undefined;
	actor SetModel( TOD_MANGLER_MODEL );   // black - never the enemy Mangler's look
	dev_log( "HELPER_MODEL ent=" + actor GetEntityNumber() + " kind=mangler model=" + actor.model );
	actor Ghost();
	tod_mangler::configure_variant( actor );   // colour / cannon fields only; NOT tod_mangler (that is the enemy's roof count)
	actor.tod_boss_custom_speed = true;
	actor.acc_boss_custom_speed = true;
	actor.ignore_enemy_count = true;
	actor.ignore_round_spawn_failsafe = true;
	actor.no_powerups = true;
	actor.disableAmmoDrop = true;
	actor.ignore_nuke = true;
	actor.health = 50000;
	actor.maxhealth = 50000;
	actor.ignoreall = true;
	actor.ignoreme = true;
	actor.team = "allies";
	// SAME FRAME AS THE SPAWN, before its first behaviour tick (user 2026-09-26:
	// "the manglers couldn't move"): on team "allies" stock's zombieFindFlesh runs
	// findZombieEnemy, which SetGoal( self.origin )s EVERY tick when no zombie
	// qualifies - that pinned both helpers of the 16:06 run for 63 s and beat
	// helper_follow. With find-flesh off, mangler_chase owns the goal.
	actor.ignore_find_flesh = true;
	actor thread mangler_init( self );
	return actor;
}

// _tod_mangler::initialize_actor's body, on the players' side
function mangler_init( owner )
{
	self endon( "death" );
	wait 0.05;
	self.allowdeath = true;
	self.gibbed = true;
	self.head_gibbed = true;
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
	self.variant_type = 0;
	self.zombie_move_speed = "sprint";
	self.zombie_arms_position = "down";
	self.ai_state = "zombie_think";
	self.find_flesh_struct_string = "find_flesh";
	self.zombie_think_done = true;
	self.zombie_init_done = true;
	self.team = "allies";
	self.updateSight = false;
	self setAvoidanceMask( "avoid none" );
	self zm_utility::disable_react();
	self zm_utility::init_zombie_run_cycle();
	self.zombie_move_speed = "sprint";
	// THE MANGLER THAT NEVER WALKED (builds 11-16): init_zombie_run_cycle -> set_zombie_run_cycle RE-ROLLS
	// variant_type (RandomInt of zm_variant_type_max, archetype zombie), and hb_mangler.ai_ast's ONLY
	// move@zombie row is _variant_type 0 - any other roll has no walk clip, so the tree sat in move@zombie
	// (has_path=1, asm running) and moved 0. _tod_mangler::initialize_actor sets it back to 0 right here;
	// this copy of that function had dropped the line. mangler_chase re-asserts it every tick too.
	self.variant_type = 0;
	self.needs_run_update = true;
	self.deathanim = %hb_mangler_death;
	self Show();
	self.ignoreall = false;
	self.hasSeenFavoriteEnemy = true;
	self SetGoal( self.origin );
	self PathMode( "move allowed" );
	self SetPlayerCollision( false );
	self clientfield::set( "tod_necro_soul", TOD_SOUL_MANGLER );
	self PushActors( true );   // the enemy's own (initialize_actor): it shoulders through the horde instead of standing behind it
	// NO STOCK MELEE (build 14 log: has_path=1, pathmode move allowed, in_play=1, not scripted - and still
	// moved 0): stock zombieShouldMeleeCondition reads the ENGINE enemy, and a helper standing in the fight
	// always has some zombie inside 64 u, which holds the tree in its melee branch - a branch this Mangler
	// has no melee for - instead of MoveBehavior. Its swings are ours (mangler_attacks).
	self.ignoreMelee = true;
	// in play from the start: stock's zombie tree only runs its PlayableArea move branch once this is set
	// (zombieEnteredPlayable flips it on touching a player_volume); stock's own function, then our no-drop back
	self zm_spawner::zombie_complete_emerging_into_playable_area();
	self.no_powerups = true;
	self notify( "zombie_init_done" );
	// NO tod_mangler::body_lights and no cannon idle glow (user 2026-09-26: its orange light turned the white
	// smoke orange): the helper's only lights are its white eyes (the csc) and its soul aura
	self thread mangler_chase( owner );
	self thread mangler_attacks( owner );
}

// the Mangler's goal is set HERE and nowhere else (ignore_find_flesh, spawn_mangler):
// toward its target, or back beside the owner. Scripted swings / shots own it meanwhile.
function mangler_chase( owner )
{
	self endon( "death" );
	for ( ;; )
	{
		wait 0.25;
		if ( !isdefined( owner ) ) return;
		if ( IS_TRUE( self.tod_necro_paused ) ) continue;
		// the enemy Mangler's own chase re-asserts its playback rate every tick (_tod_mangler::chase) and
		// it walks; ours only wrote it on pause edges and stood (build 16 log: no melee, enemy far, has_path=1,
		// asm running, floor_gap 0, scripted 0 - and moved 0 for seconds). Same write, same cadence.
		self ASMSetAnimationRate( 1 );
		if ( self.variant_type !== 0 )
		{
			dev_log( "MANGLER_VARIANT_FIX ent=" + self GetEntityNumber() + " was=" + self.variant_type );   // the walk clip exists only for 0
			self.variant_type = 0;
		}
		self.ignore_find_flesh = true;   // re-asserted: nothing may hand the goal back to stock
		t = helper_target( self, owner );
		if ( isdefined( t ) )
		{
			self.favoriteenemy = t;
			self.hasSeenFavoriteEnemy = true;
			self.v_zombie_custom_goal_pos = t.origin;
			self helper_goal( t.origin, "target", t );
		}
		else
		{
			self.favoriteenemy = undefined;
			self.v_zombie_custom_goal_pos = owner.origin;
			self helper_follow( owner );
		}
	}
}

function mangler_attacks( owner )
{
	self endon( "death" );
	next_cannon = GetTime() + 1500;
	for ( ;; )
	{
		wait 0.1;
		if ( !isdefined( owner ) ) return;
		if ( IS_TRUE( self.tod_necro_paused ) ) continue;
		t = self.favoriteenemy;
		if ( !isdefined( t ) || !IsAlive( t ) || !isdefined( t.team ) || t.team != level.zombie_team ) continue;
		d2 = DistanceSquared( self.origin, t.origin );
		if ( d2 < TOD_MANGLER_MELEE_RANGE * TOD_MANGLER_MELEE_RANGE )
		{
			face = VectorToAngles( ( t.origin[ 0 ], t.origin[ 1 ], self.origin[ 2 ] ) - self.origin );
			self AnimScripted( "note_notify", self.origin, face, %hb_mangler_melee );
			self PlaySound( "hb_mangler_melee" );
			wait 0.77;   // the clip's hit frame (_tod_mangler)
			if ( !isdefined( owner ) ) return;
			fwd = AnglesToForward( self.angles );
			n = 0;
			foreach ( z in GetAITeamArray( level.zombie_team ) )
			{
				if ( !isdefined( z ) || !IsAlive( z ) ) continue;
				v = z.origin - self.origin;
				if ( LengthSquared( v ) > TOD_MANGLER_SWEEP * TOD_MANGLER_SWEEP ) continue;
				if ( VectorDot( VectorNormalize( ( v[ 0 ], v[ 1 ], 0 ) ), ( fwd[ 0 ], fwd[ 1 ], 0 ) ) < 0.2 ) continue;
				if ( is_elite( z ) ) helper_hurt( z, round_zombie() * TOD_MANGLER_MELEE_ELITE * owner helper_elite_mult(), owner );
				else soul_kill( z, owner, self, "mangler_sweep", 0 );
				n++;
			}
			dev_log( "MANGLER_SWEEP ent=" + self GetEntityNumber() + " hit=" + n );
			wait 1.1;
			if ( isdefined( self ) ) self PathMode( "move allowed" );   // a scripted anim must never leave it pinned
		}
		else if ( d2 < TOD_MANGLER_CANNON_RANGE * TOD_MANGLER_CANNON_RANGE && GetTime() >= next_cannon )
		{
			next_cannon = GetTime() + owner pack_cannon_ms();   // PACK MASTER Lv6: 2.5 s
			aim = t.origin + ( 0, 0, 36 );
			self AnimScripted( "note_notify", self.origin, VectorToAngles( ( aim[ 0 ], aim[ 1 ], self.origin[ 2 ] ) - self.origin ), %hb_mangler_cannon, "normal", undefined, 2.0, 0.1 );
			wait 1.02;   // the clip's shoot frame at rate 2 (_tod_mangler)
			if ( !isdefined( owner ) ) return;
			if ( isdefined( t ) && IsAlive( t ) ) aim = t.origin + ( 0, 0, 36 );
			muzzle = self GetTagOrigin( "tag_flash" );
			if ( !isdefined( muzzle ) ) muzzle = self.origin + ( 0, 0, 60 );
			tod_perk_scatter::play_sound_at_origin( muzzle, "hb_mangler_fire" );
			level thread mangler_shot( self, owner, muzzle, aim );
			wait 0.53;
			if ( isdefined( self ) ) self PathMode( "move allowed" );
		}
	}
}

function mangler_shot( mangler, owner, from, to )
{
	host = Spawn( "script_model", from );
	if ( !isdefined( host ) ) return;
	host SetModel( "tag_origin" );
	host.angles = VectorToAngles( to - from );
	util::wait_network_frame();   // the client must know the host before an FX can ride it
	if ( !isdefined( host ) ) return;
	PlayFXOnTag( TOD_MANGLER_SHOT_FX, host, "tag_origin" );
	t = Distance( from, to ) / 1500;
	if ( t < 0.05 ) t = 0.05;
	host MoveTo( to, t );
	wait t;
	fx_once( TOD_MANGLER_BLAST_FX, to, 2 );
	tod_perk_scatter::play_sound_at_origin( to, "hb_mangler_impact" );
	n = 0;
	if ( isdefined( owner ) )
	{
		foreach ( z in array::get_all_closest( to, GetAITeamArray( level.zombie_team ), undefined, undefined, TOD_MANGLER_BLAST ) )
		{
			if ( !isdefined( z ) || !IsAlive( z ) ) continue;
			if ( is_elite( z ) ) helper_hurt( z, round_zombie() * TOD_MANGLER_CANNON_ELITE * owner helper_elite_mult(), owner );
			else soul_kill( z, owner, mangler, "mangler_cannon", 0 );
			n++;
		}
	}
	dev_log( "MANGLER_CANNON hit=" + n + " at=" + to );
	host Delete();
}

// =============================================================================
// shared helper life
// =============================================================================
function helper_life( owner, life )
{
	self endon( "death" );
	left = life;
	tick = 0;
	last_org = self.origin;
	still = 0;
	stuck_logged = false;
	for ( ;; )
	{
		wait 0.25;
		// HELPER_TICK once a second (user 2026-09-26: "we should have logs for all of
		// this, so let's catch any bugs"), HELPER_STUCK after 3 s unmoved with a goal
		// more than 150 away; neither changes the helper
		tick++;
		if ( isdefined( owner ) && tick % 4 == 0 )
		{
			moved = Distance( self.origin, last_org );
			last_org = self.origin;
			gd = ( isdefined( self.tod_necro_goal ) ? Int( Distance( self.origin, self.tod_necro_goal ) ) : -1 );
			if ( moved < 16 && gd > 150 && !IS_TRUE( self.tod_necro_paused ) ) still++;
			else { still = 0; stuck_logged = false; }
			fav = ( isdefined( self.favoriteenemy ) ? self.favoriteenemy GetEntityNumber() : -1 );
			asm_status = self ASMGetStatus();
			if ( !isdefined( asm_status ) ) asm_status = "none";
			dev_log( "HELPER_TICK ent=" + self GetEntityNumber() + " kind=" + self.tod_necro_kind + " org=" + self.origin + " moved=" + Int( moved )
				+ " goal_to=" + ( isdefined( self.tod_necro_goal_to ) ? self.tod_necro_goal_to : "none" ) + " goal_dist=" + gd + " fav=" + fav
				+ " owner_dist=" + Int( Distance( self.origin, owner.origin ) ) + " scripted=" + self IsPlayingAnimScripted()
				+ " ignoreall=" + IS_TRUE( self.ignoreall ) + " no_flesh=" + IS_TRUE( self.ignore_find_flesh ) + " team=" + self.team + " model=" + self.model
				+ " paused=" + IS_TRUE( self.tod_necro_paused ) + " kills=" + self.tod_necro_kills + " left_s=" + Int( left )
				+ " has_path=" + self HasPath() + " pathmode=" + self GetPathMode() + " in_play=" + IS_TRUE( self.completed_emerging_into_playable_area )
				+ " cant_move=" + IS_TRUE( self.cant_move ) + " no_melee=" + IS_TRUE( self.ignoreMelee ) + " variant=" + ( isdefined( self.variant_type ) ? self.variant_type : "none" ) + " speed=" + ( isdefined( self.zombie_move_speed ) ? self.zombie_move_speed : "none" )
				+ " enemy=" + ( isdefined( self.enemy ) ? self.enemy GetEntityNumber() + "@" + Int( Distance( self.origin, self.enemy.origin ) ) : "none" )
				+ " floor_gap=" + Int( self.origin[ 2 ] - BulletTrace( self.origin + ( 0, 0, 8 ), self.origin - ( 0, 0, 200 ), false, self )[ "position" ][ 2 ] )
				+ " attackable=" + isdefined( self.attackable ) + " enemy_override=" + isdefined( self.enemyoverride ) + " asm=" + asm_status );
			if ( still >= 3 && !stuck_logged )
			{
				stuck_logged = true;
				dev_log( "HELPER_STUCK ent=" + self GetEntityNumber() + " kind=" + self.tod_necro_kind + " org=" + self.origin + " still_s=" + still
					+ " goal=" + ( isdefined( self.tod_necro_goal ) ? self.tod_necro_goal : ( 0, 0, 0 ) ) + " goal_dist=" + gd
					+ " on_nav=" + isdefined( GetClosestPointOnNavMesh( self.origin, 32 ) ) + " fav=" + fav
					+ " has_path=" + self HasPath() + " pathmode=" + self GetPathMode() + " in_play=" + IS_TRUE( self.completed_emerging_into_playable_area ) );
			}
			if ( still >= TOD_HELPER_BLINK_S && !self IsPlayingAnimScripted() )
			{
				nav = GetClosestPointOnNavMesh( owner.origin, 128 );
				if ( isdefined( nav ) )
				{
					fx_once( "tod/necro/fx_necro_summon", self.origin, 2 );
					from = self.origin;
					self ForceTeleport( nav, self.angles );
					fx_once( "tod/necro/fx_necro_summon", nav, 2 );
					dev_log( "HELPER_BLINK ent=" + self GetEntityNumber() + " kind=" + self.tod_necro_kind + " from=" + from + " to=" + nav + " still_s=" + still );
					still = 0;
					stuck_logged = false;
					last_org = self.origin;
				}
			}
		}
		if ( !isdefined( owner ) ) { self thread helper_end( "owner_gone" ); return; }
		if ( self.team != "allies" ) self.team = "allies";   // a late stock init must never flip it back
		paused = IS_TRUE( level.tod_upgrade_pause );
		if ( paused != IS_TRUE( self.tod_necro_paused ) )
		{
			self.tod_necro_paused = paused;
			self.ignoreall = paused;
			self ASMSetAnimationRate( ( paused ? 0.05 : 1.0 ) );
		}
		if ( paused ) continue;
		left -= 0.25;
		if ( self.tod_necro_kind == "thrall" && self thrall_kill_pay( owner ) ) { self thread helper_end( "kill_limit" ); return; }
		self.tod_hpbar_frac = self helper_left_frac( owner, left, life );   // THE WHITE BAR (_tod_elite_hp)
		if ( left <= 0 ) { self thread helper_end( "expired" ); return; }
		if ( DistanceSquared( self.origin, owner.origin ) > TOD_SUMMON_LEASH * TOD_SUMMON_LEASH )
		{
			nav = GetClosestPointOnNavMesh( owner.origin, 128 );
			if ( isdefined( nav ) ) self ForceTeleport( nav, self.angles );
		}
	}
}

// THE WHITE BAR (_tod_elite_hp reads self.tod_hpbar_frac). Nothing on the horde's
// side hurts a helper, so its "health" is what is LEFT of it: the life clock, and
// for a thrall also its kills against stock Turned's limit (SUMMONING POWER raises
// it) - whichever runs out first. self = the helper.
function helper_left_frac( owner, left, life )
{
	f = 0;
	if ( life > 0 )
		f = left / life;
	if ( self.tod_necro_kind == "thrall" && isdefined( owner ) )
	{
		lim = owner thrall_kill_limit();
		if ( lim > 0 )
		{
			k = 1 - ( 1.0 * self.tod_necro_kills ) / lim;
			if ( k < f )
				f = k;
		}
	}
	if ( f < 0 )
		f = 0;
	if ( f > 1 )
		f = 1;
	return f;
}

function helper_end( why )
{
	if ( !isdefined( self ) || IS_TRUE( self.tod_necro_ending ) ) return;
	self.tod_necro_ending = true;
	dev_log( "HELPER_END ent=" + self GetEntityNumber() + " kind=" + self.tod_necro_kind + " why=" + why + " kills=" + self.tod_necro_kills
		+ " bar_frac=" + ( isdefined( self.tod_hpbar_frac ) ? self.tod_hpbar_frac : -1 ) );
	self clientfield::set( "tod_necro_soul", TOD_SOUL_RIP );   // client: the soul leaves (fx + sound)
	util::wait_network_frame();
	if ( !isdefined( self ) ) return;
	if ( self.tod_necro_kind == "thrall" && IsAlive( self ) )
	{
		// PACK MASTER Lv9: a falling thrall tears out the souls around it
		owner = self.tod_necro_owner;
		if ( isdefined( owner ) && owner pack_lv() >= 9 )
		{
			n = 0;
			foreach ( z in array::get_all_closest( self.origin, GetAITeamArray( level.zombie_team ), undefined, undefined, TOD_PACK_BURST_R ) )
			{
				if ( !isdefined( z ) || z == self || !IsAlive( z ) || isdefined( z.tod_necro_kind ) || is_elite( z ) ) continue;
				soul_kill( z, owner, self, "thrall_burst", 0.1 );
				n++;
			}
			dev_log( "THRALL_BURST ent=" + self GetEntityNumber() + " killed=" + n );
		}
		// stock Turned's end: gib and fall
		self.allowDeath = true;
		gibserverutils::gibhead( self );
		self DoDamage( self.health + 666, self.origin );
		return;
	}
	util::wait_network_frame();
	if ( isdefined( self ) ) self Delete();
}

function helper_follow( owner )
{
	if ( DistanceSquared( self.origin, owner.origin ) > 220 * 220 )
	{
		nav = GetClosestPointOnNavMesh( owner.origin, 96 );
		if ( isdefined( nav ) ) self helper_goal( nav, "owner", owner );
	}
	else if ( IS_TRUE( self.ignore_find_flesh ) && self.tod_necro_goal_to !== "hold" )
		self helper_goal( self.origin, "hold", owner );   // beside the owner: stop, do not orbit an old goal
}

// one writer for a helper's goal, logged when the KIND of goal or its entity
// changes (HELPER_GOAL: proves the chase moves, not just that nothing pins it)
function helper_goal( pos, to, ent )
{
	self SetGoal( pos );
	self.tod_necro_goal = pos;
	ent_n = ( isdefined( ent ) ? ent GetEntityNumber() : -1 );
	if ( self.tod_necro_goal_to === to && self.tod_necro_goal_ent === ent_n ) return;
	self.tod_necro_goal_to = to;
	self.tod_necro_goal_ent = ent_n;
	dev_log( "HELPER_GOAL ent=" + self GetEntityNumber() + " kind=" + self.tod_necro_kind + " to=" + to + " target=" + ent_n
		+ " dist=" + Int( Distance( self.origin, pos ) ) );
}

// the nearest zombie the helper can see, near it and near its owner
function helper_target( helper, owner )
{
	if ( isdefined( helper.tod_necro_target ) && IsAlive( helper.tod_necro_target ) && !isdefined( helper.tod_necro_target.tod_necro_binder ) && GetTime() < helper.tod_necro_target_until )
		return helper.tod_necro_target;
	best = undefined;
	bd = TOD_SUMMON_SEEK * TOD_SUMMON_SEEK;
	foreach ( z in GetAITeamArray( level.zombie_team ) )
	{
		if ( !isdefined( z ) || !IsAlive( z ) || IS_TRUE( z.marked_for_death ) ) continue;
		if ( isdefined( z.tod_necro_binder ) ) continue;   // a Necromancer is binding it (bind_start)
		if ( !IS_TRUE( z.completed_emerging_into_playable_area ) && z.archetype === "zombie" ) continue;
		d = DistanceSquared( helper.origin, z.origin );
		if ( d >= bd ) continue;
		if ( DistanceSquared( owner.origin, z.origin ) > TOD_SUMMON_SEEK_OWNER * TOD_SUMMON_SEEK_OWNER ) continue;
		if ( abs( owner.origin[ 2 ] - z.origin[ 2 ] ) > 200 ) continue;
		if ( !BulletTracePassed( helper.origin + ( 0, 0, 32 ), z.origin + ( 0, 0, 32 ), false, helper, z ) ) continue;
		best = z;
		bd = d;
	}
	helper.tod_necro_target = best;
	helper.tod_necro_target_until = GetTime() + 500;
	return best;
}

// =============================================================================
// SOUL BOMB (the lethal button; _tod_class_kit polls it)
// =============================================================================
// souls still needed (0 = ready) - the HUD's lethal tile shows it
function soul_bomb_left()
{
	if ( !isdefined( self.tod_bomb_souls ) ) return 0;
	left = self bomb_souls_need() - self.tod_bomb_souls;
	if ( left <= 0 ) return 0;
	return Int( left );
}

// a kill you made feeds the bomb one soul (src: beam / helper / drain / burn).
// The bomb's own kills and binds never call this.
function bomb_charge( src )
{
	if ( !isdefined( self ) || !IsPlayer( self ) || !self is_necro() ) return;
	if ( !isdefined( self.tod_bomb_souls ) ) self.tod_bomb_souls = 0;
	need = self bomb_souls_need();
	if ( self.tod_bomb_souls >= need ) return;   // full: nothing banks past ready
	self.tod_bomb_souls++;
	dev_log( "SOULS +1 player=" + self GetEntityNumber() + " src=" + src + " total=" + self.tod_bomb_souls + " need=" + need );
	if ( self.tod_bomb_souls >= need )
	{
		dev_log( "BOMB ready player=" + self GetEntityNumber() + " souls=" + self.tod_bomb_souls + " lv=" + self bomb_lv() );
		tod_ability_fx::kit_ready( self, "pulse" );   // PK18: the Soul Pulse fully charged has its own sting
	}
}

function soul_bomb_fire( unlimited )
{
	if ( IS_TRUE( self.tod_necro_pulse_busy ) ) return false;
	if ( !IS_TRUE( unlimited ) && self soul_bomb_left() > 0 )
	{
		dev_log( "BOMB_DENY player=" + self GetEntityNumber() + " why=charging souls=" + self.tod_bomb_souls + " need=" + self bomb_souls_need() );
		tod_ability_fx::kit_deny( self, "soul_pulse", "charging" );   // PK18
		return false;
	}
	if ( !IS_TRUE( unlimited ) ) self.tod_bomb_souls = 0;   // spent: charge it again with kills
	org = self.origin;
	radius = self bomb_radius();
	band = Int( ( radius - TOD_BOMB_RING_R0 + TOD_BOMB_RING_STEP / 2 ) / TOD_BOMB_RING_STEP );
	if ( band < 0 ) band = 0;
	if ( band > 3 ) band = 3;
	self clientfield::set( "tod_necro_bomb_band", band );   // the ring's size, read by the csc on the counter below
	self clientfield::increment( "tod_necro_bomb" );   // client: the souls + the ground ring (_tod_necro_skull.csc)
	tod_ability_fx::soul_pulse( self, band );   // docs/203: the soul DOME (fog, rings, lights, motes) under the ring + a soul mist on the caster's camera + the soul's sound in both ears
	self staff_pulse_pose();
	tod_perk_scatter::play_sound_at_origin( org, "evt_zombie_skull_scream", 4 );
	Earthquake( 0.35, 0.6, org, 600 );
	self PlayRumbleOnEntity( "damage_heavy" );
	killed = 0;
	elites = 0;
	// timed to the ring (user 2026-09-26: "the zombie should die exactly when the blast hits it"):
	// a victim waits TOD_BOMB_WAVE_MS x its distance / the radius, then soul_kill_run's one network frame
	foreach ( z in array::get_all_closest( org, GetAITeamArray( level.zombie_team ), undefined, undefined, radius ) )
	{
		if ( !isdefined( z ) || !IsAlive( z ) ) continue;
		// each victim goes as the ring sweeps over it (user: "die exactly when the blast hits")
		delay = ( TOD_BOMB_WAVE_MS / 1000 ) * Distance2D( z.origin, org ) / radius;
		if ( is_elite( z ) )
		{
			z thread bomb_elite( self, delay );
			elites++;
		}
		else
		{
			soul_kill( z, self, undefined, "soul_bomb", delay );
			killed++;
		}
	}
	dev_log( "BOMB spent player=" + self GetEntityNumber() + " souls=" + killed + " elites=" + elites + " radius=" + radius
		+ " lv=" + self bomb_lv() + " need_next=" + self bomb_souls_need() + " unlimited=" + IS_TRUE( unlimited ) + " elite_zombies=" + self bomb_elite_zombies()
		+ " ring_band=" + band + " wave_ms=" + TOD_BOMB_WAVE_MS );
	return true;
}

// The native weapon raise slot owns the brief staff thrust. An item proxy does
// not occupy a primary slot or change the soul meter. Level-owned cleanup also
// runs after death; an old cast never replaces the player's new weapon choice.
function staff_pulse_pose()
{
	w = self GetCurrentWeapon();
	if ( !isdefined( w ) || !isdefined( w.name ) ) return;
	if ( IsSubStr( w.name, "tod_necro_staff2" ) ) name = "tod_necro_pulse2";
	else if ( IsSubStr( w.name, "tod_necro_staff3" ) ) name = "tod_necro_pulse3";
	else return;
	proxy = GetWeapon( name );
	if ( !isdefined( proxy ) || proxy == level.weaponNone )
	{
		dev_log( "STAFF_PULSE_FAIL reason=asset_missing weapon=" + name );
		return;
	}
	token = GetTime();
	self.tod_necro_pulse_busy = true;
	self.tod_necro_pulse_token = token;
	self GiveWeapon( proxy );
	self ShouldDoInitialWeaponRaise( proxy, true );
	self SwitchToWeaponImmediate( proxy );
	dev_log( "STAFF_PULSE_START player=" + self GetEntityNumber() + " token=" + token + " previous=" + w.name + " proxy=" + name );
	level thread staff_pulse_restore( self, w, proxy, token );
}

function staff_pulse_restore( owner, previous, proxy, token )
{
	level endon( "end_game" );
	started = GetTime();
	pose_logged = false;
	while ( isdefined( owner ) && IsAlive( owner ) && GetTime() - started < 650 )
	{
		if ( owner laststand::player_is_in_laststand() ) break;
		wait 0.05;
		if ( isdefined( owner ) && !pose_logged )
		{
			dev_log( "STAFF_PULSE_POSE player=" + owner GetEntityNumber() + " token=" + token + " selected=" + ( owner GetCurrentWeapon() == proxy ) );
			pose_logged = true;
		}
	}
	if ( !isdefined( owner ) || owner.tod_necro_pulse_token !== token ) return;
	current = owner GetCurrentWeapon();
	current_name = "none";
	if ( isdefined( current ) && isdefined( current.name ) ) current_name = current.name;
	dev_log( "STAFF_PULSE_RESULT player=" + owner GetEntityNumber() + " token=" + token + " selected=" + ( current == proxy ) + " current=" + current_name + " owned=" + owner HasWeapon( proxy ) + " pose=original_staff" );
	if ( IsAlive( owner ) && !owner laststand::player_is_in_laststand() && owner GetCurrentWeapon() == proxy && owner HasWeapon( previous ) )
	{
		owner ShouldDoInitialWeaponRaise( previous, false );
		owner SwitchToWeaponImmediate( previous );
	}
	if ( owner HasWeapon( proxy ) ) owner TakeWeapon( proxy );
	owner.tod_necro_pulse_busy = false;
	owner.tod_necro_pulse_token = undefined;
	dev_log( "STAFF_PULSE_END player=" + owner GetEntityNumber() + " token=" + token + " elapsed_ms=" + ( GetTime() - started ) );
}

function bomb_elite( owner, delay )
{
	self endon( "death" );
	util::wait_network_frame();   // lands with the plain zombies' deaths (soul_kill_run's frame)
	if ( delay > 0 ) wait delay;
	if ( isdefined( owner ) ) hurt( self, round_zombie() * owner bomb_elite_zombies(), owner );
	if ( isdefined( self ) && IsAlive( self ) ) tod_ability_fx::actor_soul( self );   // docs/203: an elite struck shows the soul-rip flash (it used to show nothing)
}

// =============================================================================
// shared: take a zombie's soul
// =============================================================================
function soul_kill( z, owner, helper, why, delay )
{
	if ( !isdefined( z ) || IS_TRUE( z.marked_for_death ) ) return;
	// A ZOMBIE SOMEONE IS BINDING IS SPARED (LT-fix 2026-10-05): the hound bite, the Mangler sweep / cannon, the Lv9
	// thrall burst and the soul bomb all end here (older runs: a bound zombie died 50-150 ms after a MANGLER_SWEEP /
	// MANGLER_CANNON). It must not be MARKED either: marked_for_death would make this function skip it again when
	// bind_finish tears its soul out for a hound / Mangler, leaving it alive under the new helper. bind_finish clears
	// the binder before its own soul_kill.
	if ( isdefined( z.tod_necro_binder ) )
	{
		dev_log( "SOUL_SPARED target=" + z GetEntityNumber() + " why=" + why + " binder=" + z.tod_necro_binder GetEntityNumber() );
		return;
	}
	z.marked_for_death = true;
	z thread soul_kill_run( owner, helper, why, delay );
}

function soul_kill_run( owner, helper, why, delay )
{
	self endon( "death" );
	if ( delay > 0 ) wait delay;
	self clientfield::set( "tod_necro_soul", TOD_SOUL_RIP );
	util::wait_network_frame();
	if ( !isdefined( self ) || !IsAlive( self ) ) return;
	if ( isdefined( owner ) )
	{
		// PAY FIRST: this thread endon( "death" )s and DoDamage raises the death inside
		// the call, so nothing after the killing blow runs (build 11: every helper
		// kill and every bomb refund was lost that way). The kill below is certain.
		if ( why == "soul_bomb" ) refund( owner, TOD_BOMB_REFUND );
		else if ( why != "beam" && why != "bind" ) pay_kill( owner, helper, why, true );   // the beam refunded in _tod_necro_skull; a bind is a spend
		self DoDamage( self.health + 666, self.origin, owner, owner, "none", "MOD_UNKNOWN" );   // kill intent: exempt from the power scale
	}
	else
		self DoDamage( self.health + 666, self.origin );
}

// a helper's kill: the owner is paid points (a DoDamage kill already paid the
// stock kill points, so only the swing kills - which have no attacker - pay here)
// and souls
function pay_kill( owner, helper, why, stock_paid )
{
	if ( !isdefined( owner ) ) return;
	if ( !IS_TRUE( stock_paid ) )
	{
		kill_pts = TOD_SUMMON_KILL_PTS;
		// THE HAVENS (docs/202): an owner standing inside a safe-zone field is paid a quarter
		if ( isdefined( level.tod_haven_kill_pay_fn ) ) kill_pts = [[ level.tod_haven_kill_pay_fn ]]( owner, kill_pts );
		owner zm_score::add_to_player_score( kill_pts );
	}
	refund( owner, TOD_SUMMON_REFUND );
	owner bomb_charge( "helper" );
	summon_hp_kill( owner );
	if ( isdefined( helper ) )
	{
		if ( why != "thrall_swing" ) helper.tod_necro_kills++;
		if ( helper.tod_necro_kills <= 3 || helper.tod_necro_kills % 5 == 0 )
			dev_log( "HELPER_KILL ent=" + helper GetEntityNumber() + " kind=" + helper.tod_necro_kind + " how=" + why + " kills=" + helper.tod_necro_kills );
	}
}

// SUMMONER MASTER (card, 2026-09-27): one helper kill = one call (_tod_class_cards::summon_kill,
// which checks the card, the class and full health). THE HELPER KILL PATHS, each reaching this
// exactly once: thrall swings (thrall_kill_pay -> pay_kill), hound bites / Mangler sweeps /
// Mangler cannon / the Lv9 thrall burst on ordinary zombies (soul_kill -> pay_kill), and a
// helper's authored hit that finishes an ELITE (helper_hurt; those deaths are the owner's stock
// kill and never reached pay_kill, so they do not pay the helper refund or bomb charge either).
function summon_hp_kill( owner )
{
	if ( isdefined( owner ) && isdefined( level.tod_cc_summon_kill_fn ) )
		owner [[ level.tod_cc_summon_kill_fn ]]();
}

// a helper's authored hit on an elite: counts for SUMMONER MASTER when it is the killing blow
function helper_hurt( victim, dmg, owner )
{
	if ( !isdefined( victim ) || !IsAlive( victim ) ) return;
	hurt( victim, dmg, owner );
	if ( !isdefined( victim ) || !IsAlive( victim ) ) summon_hp_kill( owner );
}

function refund( owner, n )
{
	if ( !isdefined( owner ) || !isdefined( owner.tod_necro_meter ) ) return;
	owner.tod_necro_meter = min( TOD_SUMMON_METER_MAX, owner.tod_necro_meter + n );
}

// =============================================================================
// shared helpers
// =============================================================================
// the same rule as _tod_necro_skull::is_elite
function is_elite( ai )
{
	if ( ai.archetype !== "zombie" ) return true;
	if ( isdefined( ai.tod_boss_kind ) ) return true;
	if ( IS_TRUE( ai.ignore_nuke ) ) return true;
	if ( IS_TRUE( ai.tod_golden ) ) return true;   // THE GOLDEN ZOMBIE (_tod_golden_zombie, 2026-09-29): never bound, helpers hurt it like an elite
	return false;
}

function round_zombie()
{
	if ( isdefined( level.zombie_health ) ) return level.zombie_health;
	return 14;
}

// authored damage: rides the tod_cleave_hit pass-through (no card or power-scale
// re-multiply), attacker = the Necromancer so kills pay and count
function hurt( victim, dmg, attacker )
{
	if ( !isdefined( victim ) || !IsAlive( victim ) || dmg <= 0 ) return;
	victim.tod_cleave_hit = true;
	victim DoDamage( int( dmg + 0.5 ), victim.origin, attacker, attacker, "none", "MOD_UNKNOWN", 0 );
	if ( isdefined( victim ) && IS_TRUE( victim.tod_cleave_hit ) ) victim.tod_cleave_hit = undefined;
}

// a one-shot server effect needs a tag_origin host (server PlayFX does not render)
// AND one network frame before it plays: an FX on a host the client has not
// received yet is dropped (the teleporter / King cone fix, docs/143)
function fx_once( fx, org, life )
{
	host = Spawn( "script_model", org );
	if ( !isdefined( host ) ) return;
	host SetModel( "tag_origin" );
	host thread fx_host_run( fx, life );
}

function fx_host_run( fx, life )
{
	util::wait_network_frame();
	if ( !isdefined( self ) ) return;
	PlayFXOnTag( fx, self, "tag_origin" );
	wait life;
	if ( isdefined( self ) ) self Delete();
}
