// THE WARRIOR'S SWINGS (2026-09-26, the user's first Warrior playtest: "it doesn't
// feel like I'm hitting anything ... the gauntlet ... should kill things as it's
// lunging ... it's super late ... it can only kill one at a time ... the gold battle
// sword ... can hit multiple zombies with one swing").
//
// The engine's melee lands on ONE target. Each Warrior weapon's crowd behaviour
// lived in a script that never came across with the weapon:
//   ONE INCH PUNCH  stock _zm_weap_one_inch_punch::monitor_melee_swipe: a 35-degree
//                   cone, full damage to 64 u, half to 100 u, kills flung.
//   GAUNTLET        stock _zm_weap_dragon_gauntlet: every 0.1 s for 1 s of the juke
//                   (the lunge) everything within 96 u of where you are about to be
//                   is hit; the swing itself hits everything within 128 u of the fist.
//   GOLD SWORD      Hellbound (_tod_warrior_melee / _tod_citadel_swords): a wide first
//                   stroke, then a second stroke 0.40 s later (the slash clip's second
//                   blade pass). Here both strokes take the whole arc, not one target.
// Damage is the blade's own (tod_classes::melee_dmg) through the normal melee chain
// (cards, power scale, elite rules), never a kill-all. The engine's own target is
// skipped on the first pass (tod_actor_cb_ms, stamped by upgrade_damage_cb).
// Ordinary zombies killed by a Warrior blade are flung (ragdoll), elites never.
//
// BUILD-6 PLAYTEST (2026-09-26, user):
//   GAUNTLET - "two hits, one for a regular punch, one for the dash punch ... you
//     can't just keep spamming it": the swing no longer jukes (meleeJuke 0 in
//     gen_tod_twins). (The AIM dash punch built for this was retired the same day.)
//   SWORD - "there is no sound effect when you're actually slashing a zombie,
//     which was also from Hellbound": hb_citadel_hit at the contact point on every
//     sword melee hit (Hellbound's on_caliburn_melee_hit), from the same per-hit
//     hook the hit markers use (zm::register_zombie_damage_override_callback).
//   PUNCH - the kill "a second after": a press-to-hit clock (press_to_hit_ms on
//     every SWING line) so the next log measures it.
// BUILD-9 ASK (2026-09-26, user):
//   GAUNTLET - "a lunge punch we need to remove that": the AIM dash punch is
//     RETIRED WHOLE. "a right left hook ... the left hook will be a little bit
//     weaker": the engine alternates the gauntlet's meleeAnim (its own right swipe)
//     and meleeLeftAnim (BO3's boxing-glove left punch, gen_tod_twins); every
//     weapon_melee advances hook_advance() in the same order, and the left hand
//     lands x TOD_WM_HOOK_LEFT_MULT - the engine's own hit through
//     _tod_upgrades upgrade_damage_cb (level.tod_wm_hit_mult_fn), the crowd sweep
//     here. HOOK side=L|R logs every gauntlet swing.
//   GRAVITY SMASH charges on kills (_tod_class_kit gs_charge): every kill a player
//     makes is forwarded from on_zombie_death (level.tod_gs_charge_fn).
// Logs: [TOD_WMELEE] (dev).
#using scripts\codescripts\struct;
#using scripts\shared\callbacks_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm;
#using scripts\zm\_zm_spawner;
#using scripts\zm\zm_tod2_cybercity\_tod_classes;

#insert scripts\shared\shared.gsh;

#precache( "fx", "dlc5/tomb/fx_one_inch_punch_impact" );
#precache( "fx", "dlc3/stalingrad/fx_dragon_gauntlet_melee_impact" );

#namespace tod_warrior_melee;

#define TOD_WM_SETTLE           0.05   // s: the engine's own hit lands first
#define TOD_WM_ENGINE_WINDOW    100    // ms: a victim damaged this recently was the engine's target
#define TOD_WM_HEIGHT_TOL       80

#define TOD_WM_PUNCH_DOT        0.82   // cos 35
#define TOD_WM_PUNCH_FULL       64
#define TOD_WM_PUNCH_REACH      100
#define TOD_WM_PUNCH_MAX        6

#define TOD_WM_GAUNT_SWING_R    128
#define TOD_WM_GAUNT_FIST       48     // u ahead of the body: where the swing's circle sits
#define TOD_WM_GAUNT_JUKE_R     96
#define TOD_WM_GAUNT_JUKE_MS    1000
#define TOD_WM_GAUNT_JUKE_STEP  0.1
#define TOD_WM_GAUNT_MAX        8
#define TOD_WM_HOOK_LEFT_MULT   0.5    // the gauntlet's left hook lands x0.5 (2026-09-27, user: "the left hand should do half damage"; was x0.75)
// THE LEFT-HAND TWINS (build 18, lead-approved experiment; user after build 16: "I see
// right punches, right punches, right punches over and over, but nothing with the
// left"). BO3 never alternates hands on the fire button (build 17: a bulletweapon drops
// meleeAltAnim), so every gauntlet form has a "<form>_l" twin whose swing IS BO3's
// boxing-glove left punch (gen_tod_twins GAUNTLET_ALT_TWINS - LOCKSTEP). A right swing
// ends -> the left twin is swapped in; a left swing ends, or TOD_WM_ALT_IDLE_MS pass with
// no punch, or USE is pressed -> the right comes back. The twin in hand IS the hand, so
// the left hook's x0.75 is no longer a guess. Logs: SWING (hand, same-hand repeats),
// ALT_SWAP / ALT_REVERT / ALT_SKIP, PRESS_DROPPED. 0 = the right-only gauntlet (the
// twins still link but are never given).
//
// STRICT RIGHT-LEFT (2026-09-27, user: "it should keep going right left right left ...
// sometimes it can bug out where it hits the right twice"). The user's 18:25 log had two
// causes: (1) every mid-chain repeat came exactly one clip (600-650 ms) after the last
// swing - the engine starts the next swing on the SAME weapon the instant the clip ends,
// before the swap to the other hand lands; (2) the 900 ms idle reset handed the right
// hand back between punches at the user's own 1.0-1.8 s rhythm. Now the last server frame
// of each clip BLOCKS a new swing (fire + melee, TOD_WM_ALT_BLOCK_LEAD_MS) until the other
// hand is in hand, the engine's own press queue is off on every gauntlet form
// (gen_tod_twins meleeQueueMeleeEarlyTime 0 - it could only ever queue onto the old
// hand), and the idle reset waits TOD_WM_ALT_IDLE_MS 3 s. Logs: ALT_BLOCK / ALT_UNBLOCK /
// PRESS_BLOCKED.
#define TOD_GAUNTLET_ALT_TWINS    1
#define TOD_WM_ALT_IDLE_MS        3000   // ms with no punch -> the right hand again (a fresh combo); was 900
#define TOD_WM_ALT_DROP_MS        900    // ms: a gauntlet press with no swing after it = a dropped press
#define TOD_WM_ALT_BLOCK_LEAD_MS  50     // ms before the clip's end: no new swing until the other hand is up
#define TOD_WM_ALT_BLOCK_MAX_MS   400    // the watchdog: a block older than this is always released

#define TOD_WM_SWORD_DOT        0.60   // ~53 degrees each side
#define TOD_WM_SWORD_REACH      120
#define TOD_WM_SWORD_MAX        4
#define TOD_WM_SWORD_SECOND     0.40
#define TOD_WM_SWORD_HIT_SOUND  "hb_citadel_hit"   // tod_expected_roster.csv (4 variants)
// MELEE RANGE (card "meleerange", id 31, user 2026-09-26 after build 11: "one upgrade
// for ranged, increasing your range ... for hitting what the melee is"): every crowd
// sweep's reach x( 1 + 0.15 / Lv ), max 5 (punch cone 100 -> 175, gauntlet 128 -> 224,
// sword 120 -> 210). The engine's own single-target hit is unchanged. LOCKSTEP:
// add_domain( "meleerange", ..., 5 ) in _tod_upgrades.gsc and tod_upgrade.lua DETAIL[31].
#define TOD_WM_RANGE_STEP       0.10   // 2026-09-28: ARMS SPECIALIST's reach, +10% / Lv (+90% at Lv9 = the old MELEE RANGE max; that card is retired into it)
// CLEAVE (2026-09-27 class pass 4 (user), key "sweep", user: "an upgrade on how many zombies it can hit
// with one swing. Similar to cleave ... 9 levels ... 33% ... max is 4" + "Yes: 1 zombie base,
// card earns more"): WITHOUT the card a swing hits only its target (the free crowd sweeps
// - punch +6, gauntlet +8, sword +4 - are gone). Each swing rolls its extra zombies:
// Lv/3 guaranteed + a 33% chance per level of one more (Lv3 = 2 zombies, Lv6 = 3, Lv9 = 4).
#define TOD_WM_CLEAVE_MAX_LV    9
#define TOD_WM_CLEAVE_MAX_EXTRA 3
#define TOD_WM_RANGE_MAX_LV     9   // ARMS SPECIALIST's 9 levels (2026-09-28; 6 while MELEE RANGE was its own card)

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_WMELEE] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function init()
{
	callback::on_spawned( &on_spawned );
	zm_spawner::register_zombie_death_event_callback( &on_zombie_death );
	zm::register_zombie_damage_override_callback( &on_actor_hit );
	level.tod_wm_hit_mult_fn = &hook_mult;   // read by _tod_upgrades upgrade_damage_cb (the engine's own hit)
	if ( TOD_GAUNTLET_ALT_TWINS ) level.tod_wm_alt_right_fn = &alt_right_for;   // read by _tod_class_kit bash_run (the Bash hands back to the right hand)
	level.tod_wm_hit_logs = 0;
	dev_log( "INIT punch=cone" + TOD_WM_PUNCH_REACH + "/dot" + TOD_WM_PUNCH_DOT + " gauntlet=swing" + TOD_WM_GAUNT_SWING_R + " hook_left_mult=" + TOD_WM_HOOK_LEFT_MULT + " sword=arc" + TOD_WM_SWORD_REACH + "x2(+" + TOD_WM_SWORD_SECOND + "s) sword_hit_sound=" + TOD_WM_SWORD_HIT_SOUND + " cleave_max_extra=" + TOD_WM_CLEAVE_MAX_EXTRA + " range_step=" + TOD_WM_RANGE_STEP + "/Lv max_lv=" + TOD_WM_RANGE_MAX_LV );
}

function on_spawned()
{
	self alt_block( false, "spawn" );
	self.tod_wm_sweeping = undefined;
	self thread swing_watch();
	self thread juke_watch();
	self thread input_watch();
}

// One poll per player per server frame, only while a Warrior blade is held:
// the swing buttons' rising edge -> tod_wm_press_ms (the press-to-hit clock).
function input_watch()
{
	self endon( "disconnect" );
	self endon( "death" );
	self notify( "tod_wm_input_watch" );
	self endon( "tod_wm_input_watch" );
	swing_was = true;
	for ( ;; )
	{
		wait 0.05;
		// the swap-window block's watchdog: never leave a player unable to swing
		if ( isdefined( self.tod_wm_alt_block_ms ) && GetTime() - self.tod_wm_alt_block_ms > TOD_WM_ALT_BLOCK_MAX_MS ) self alt_block( false, "watchdog" );
		kind = blade_kind( self GetCurrentWeapon() );
		if ( !isdefined( kind ) ) { swing_was = true; continue; }
		swing = ( self AttackButtonPressed() || self MeleeButtonPressed() );
		if ( swing && !swing_was )
		{
			self.tod_wm_press_ms = GetTime();
			if ( isdefined( self.tod_wm_alt_block_ms ) ) dev_log( "PRESS_BLOCKED player=" + self GetEntityNumber() + " form=" + self GetCurrentWeapon().name + " block_ms=" + ( GetTime() - self.tod_wm_alt_block_ms ) );
			// the press that STARTED a swing can be read here after hook_advance cleared
			// it (same frame): that is an answered press, not a dropped one
			answered = ( isdefined( self.tod_wm_hook_ms ) && GetTime() - self.tod_wm_hook_ms <= 100 );
			if ( kind == "gauntlet" && !answered && !isdefined( self.tod_wm_press_pending_ms ) ) self.tod_wm_press_pending_ms = GetTime();
		}
		swing_was = swing;
		if ( kind == "gauntlet" ) self alt_input_tick();
	}
}

function press_to_hit()
{
	if ( !isdefined( self.tod_wm_press_ms ) ) return -1;
	return GetTime() - self.tod_wm_press_ms;
}

// "punch" / "gauntlet" / "sword", or undefined for anything that is not a Warrior
// blade (the bash proxies tod_bash_* and hb_warrior_bash_* are not "cc_").
function blade_kind( w )
{
	if ( !isdefined( w ) || !isdefined( w.name ) ) return undefined;
	if ( IsSubStr( w.name, "cc_punch" ) ) return "punch";
	if ( IsSubStr( w.name, "cc_gauntlet" ) ) return "gauntlet";
	if ( IsSubStr( w.name, "cc_gold_sword" ) ) return "sword";
	return undefined;
}

function can_swing()
{
	if ( !isdefined( self ) || !IsAlive( self ) ) return false;
	if ( self laststand::player_is_in_laststand() ) return false;
	return true;
}

function is_elite( e )   // tod_class_kit::is_elite's list
{
	if ( !isdefined( e ) ) return false;
	return ( IS_TRUE( e.is_boss ) || IS_TRUE( e.acc_is_boss ) || IS_TRUE( e.acc_is_mini_boss )
	      || isdefined( e.tod_boss_kind ) );
}

function enemies()
{
	team = ( isdefined( level.zombie_team ) ? level.zombie_team : "axis" );
	return GetAITeamArray( team );
}

// ---------------------------------------------------------------------------
// The swing (fire or melee button, lunge or not)
// ---------------------------------------------------------------------------
function swing_watch()
{
	self endon( "disconnect" );
	self endon( "death" );
	self notify( "tod_wm_swing_watch" );
	self endon( "tod_wm_swing_watch" );
	for ( ;; )
	{
		note = self util::waittill_any_return( "weapon_melee", "weapon_melee_power", "weapon_melee_charge" );
		w = self GetCurrentWeapon();
		kind = blade_kind( w );
		if ( !isdefined( kind ) ) continue;
		token = GetTime();
		side = undefined;
		if ( kind == "gauntlet" )
		{
			side = self hook_advance( w );
			if ( TOD_GAUNTLET_ALT_TWINS ) self thread alt_after_swing( w );
		}
		wait TOD_WM_SETTLE;
		if ( !( self can_swing() ) || self GetCurrentWeapon() != w )
		{
			dev_log( "SWING_SKIP player=" + self GetEntityNumber() + " kind=" + kind + " reason=" + ( self can_swing() ? "weapon_changed" : "down_or_dead" ) );
			continue;
		}
		reach = self reach_mult();
		extra = self cleave_extra();   // CLEAVE: this swing's extra zombies (0 without the card)
		extra += self reach_bonus( token );   // ARMS SPECIALIST's reach: a whiff reaches the nearest zombie
		if ( kind == "punch" )
		{
			// NO LUNGE (user 2026-10-05: "remove the lunge altogether ... So just punching and then using our
			// calculated radius"): a punch the engine landed on nobody takes the first zombie inside this cone
			// (35 deg, full damage to 64 u, half to 100 u), so it connects at the cone's reach without the dash.
			// Until now the cone's budget was CLEAVE's alone - 0 without the card - so a missed punch hit nothing.
			if ( extra < 1 && !( self engine_landed( token ) ) ) extra = 1;
			self sweep_cone( w, kind, note, TOD_WM_PUNCH_DOT, TOD_WM_PUNCH_REACH * reach, TOD_WM_PUNCH_FULL * reach, extra, token, true );
		}
		else if ( kind == "gauntlet" )
		{
			fwd = self flat_forward();
			mult = ( side == "L" ? TOD_WM_HOOK_LEFT_MULT : 1.0 );
			dev_log( "HOOK side=" + side + " mult=" + mult + " player=" + self GetEntityNumber() + " weapon=" + w.name + " note=" + note + " clip=" + ( side == "L" ? "vm_tod_gauntlet_left_hook" : "vm_z_aint_no_dragon_melee_swipe" ) );
			PhysicsExplosionCylinder( self.origin + fwd * TOD_WM_GAUNT_FIST * reach + ( 0, 0, 40 ), 96, 48, 1.5 );   // stock's debris shove
			self sweep_radius( w, kind, note, self.origin + fwd * TOD_WM_GAUNT_FIST * reach + ( 0, 0, 40 ), TOD_WM_GAUNT_SWING_R * reach, extra, token, true, mult );
		}
		else
		{
			self sweep_cone( w, kind, note, TOD_WM_SWORD_DOT, TOD_WM_SWORD_REACH * reach, undefined, extra, token, true );
			self thread sword_second( w, token, reach, extra );
		}
	}
}

// CLEAVE: the extra zombies for one swing (self = player). Lv/3 guaranteed, then a
// (Lv % 3) in 3 chance of one more; capped at TOD_WM_CLEAVE_MAX_EXTRA.
function cleave_extra()
{
	lv = 0;
	if ( isdefined( self.tod_levels ) && isdefined( self.tod_levels[ "sweep" ] ) ) lv = Int( self.tod_levels[ "sweep" ] );
	if ( lv <= 0 ) return 0;
	if ( lv > TOD_WM_CLEAVE_MAX_LV ) lv = TOD_WM_CLEAVE_MAX_LV;
	e = Int( lv / 3 );
	rem = lv % 3;
	if ( rem > 0 && RandomInt( 3 ) < rem ) e++;
	if ( e > TOD_WM_CLEAVE_MAX_EXTRA ) e = TOD_WM_CLEAVE_MAX_EXTRA;
	return e;
}

// MELEE RANGE ON ITS OWN (2026-09-28, user: every card must do something when taken):
// without CLEAVE a swing's sweeps had a budget of 0, so the longer reach touched nothing
// and the card was dead alone. Now a swing the engine landed on NOBODY (it whiffed at the
// blade's native reach) hits the nearest zombie inside the card's longer reach instead.
// A swing that connected gets nothing extra - the crowd is still CLEAVE's job.
// self = player; token = the swing's GetTime(). on_actor_hit stamps tod_wm_engine_hit_ms.
function reach_bonus( token )
{
	if ( self reach_mult() <= 1 ) return 0;
	if ( self engine_landed( token ) ) return 0;
	ms = self.tod_wm_engine_hit_ms;
	dev_log( "RANGE_WHIFF player=" + self GetEntityNumber() + " reach_mult=" + self reach_mult() + " last_engine_hit_age=" + ( isdefined( ms ) ? ( token - ms ) : -1 ) );
	return 1;
}

// did the ENGINE's own melee land on anyone for this swing? (on_actor_hit stamps tod_wm_engine_hit_ms; the
// engine's hit lands before the sweep's TOD_WM_SETTLE wait ends - a punch kill is already gone from the pool)
function engine_landed( token )
{
	ms = self.tod_wm_engine_hit_ms;
	return ( isdefined( ms ) && ms >= token - TOD_WM_ENGINE_WINDOW );
}

// REACH: 1 + 0.10 / ARMS SPECIALIST Lv (user 2026-09-28: "move melee range upgrade inside of arms
// specialist"; the MELEE RANGE card, key meleerange, is retired).
function reach_mult()
{
	lv = 0;
	if ( isdefined( self.tod_levels ) && isdefined( self.tod_levels[ "heavyhands" ] ) ) lv = Int( self.tod_levels[ "heavyhands" ] );
	if ( lv < 0 ) lv = 0;
	if ( lv > TOD_WM_RANGE_MAX_LV ) lv = TOD_WM_RANGE_MAX_LV;
	return 1 + TOD_WM_RANGE_STEP * lv;
}

// A blade form's swing-time step from its MELEE SPEED rung (_kN).
// LOCKSTEP gen_tod_twins.js KNIFE_STEP k0..k5.
function swing_scale( w )
{
	steps = array( 1.0, 0.85, 0.76, 0.70 );   // 2026-09-28: k0..k3 (the unused k1 / k3 retired); ARMS SPECIALIST Lv3 / 6 / 9   // 2026-09-28: ARMS SPECIALIST -15 / -24 / -30% at Lv3 / 6 / 9 (k2 / k4 / k5)
	if ( !isdefined( w ) || !isdefined( w.name ) ) return 1.0;
	for ( i = steps.size - 1; i > 0; i-- )
		if ( IsSubStr( w.name, "_k" + i ) ) return steps[ i ];
	return 1.0;
}

function flat_forward()
{
	a = self GetPlayerAngles();
	return AnglesToForward( ( 0, a[ 1 ], 0 ) );
}

// The slash clip's second blade pass (Hellbound: frame 21 against the first at 9).
// A new swing, a weapon change or a death cancels it.
function sword_second( w, token, reach, extra )
{
	self endon( "disconnect" );
	self endon( "death" );
	self endon( "weapon_change" );
	self endon( "weapon_melee" );
	self endon( "weapon_melee_power" );
	// MELEE SPEED (2026-09-26): the sword's k rungs swing faster, and meleeTime is the
	// clip's playback length, so the second blade pass comes sooner by the same step
	wait( TOD_WM_SWORD_SECOND * swing_scale( w ) - TOD_WM_SETTLE );
	if ( !( self can_swing() ) || self GetCurrentWeapon() != w ) return;
	// the second pass is script-only (the engine never lands it), so it re-hits the target: 1 + CLEAVE's extras
	if ( !isdefined( extra ) ) extra = 0;
	self sweep_cone( w, "sword", "second_stroke", TOD_WM_SWORD_DOT, TOD_WM_SWORD_REACH * reach, undefined, 1 + extra, token + 1, false );
}

// Everything in a flat cone ahead, nearest first. full = the distance inside which
// the hit is full damage (half beyond it); undefined = full everywhere.
function sweep_cone( w, kind, note, dot, reach, full, max_hits, token, skip_engine )
{
	eye = self GetEye();
	fwd = self flat_forward();
	now = GetTime();
	dmg = tod_classes::melee_dmg( w );
	pool = util::get_array_of_closest( self.origin, enemies(), undefined, undefined, reach );
	hits = 0;
	engine = 0;
	blocked = 0;
	foreach ( z in pool )
	{
		if ( hits >= max_hits ) break;
		if ( !isdefined( z ) || !IsAlive( z ) ) continue;
		if ( Abs( z.origin[ 2 ] - self.origin[ 2 ] ) > TOD_WM_HEIGHT_TOL ) continue;
		to = z.origin - self.origin;
		d = Length( ( to[ 0 ], to[ 1 ], 0 ) );
		if ( d > reach ) continue;
		if ( d > 1 && VectorDot( VectorNormalize( ( to[ 0 ], to[ 1 ], 0 ) ), fwd ) < dot ) continue;
		if ( isdefined( z.tod_wm_token ) && z.tod_wm_token == token ) continue;
		if ( skip_engine && isdefined( z.tod_actor_cb_ms ) && now - z.tod_actor_cb_ms <= TOD_WM_ENGINE_WINDOW + TOD_WM_SETTLE * 1000 ) { engine++; continue; }
		if ( !BulletTracePassed( eye, z.origin + ( 0, 0, 40 ), false, self ) ) { blocked++; continue; }
		z.tod_wm_token = token;
		amount = dmg;
		if ( isdefined( full ) && d > full ) amount = Int( dmg * 0.5 );
		self.tod_wm_sweeping = true;
		z DoDamage( amount, z.origin, self, self, "torso", "MOD_MELEE", 0, w );
		self.tod_wm_sweeping = undefined;
		self hit_tell( kind, z );
		hits++;
	}
	dev_log( "SWING player=" + self GetEntityNumber() + " kind=" + kind + " note=" + note + " weapon=" + w.name + " dmg=" + dmg + " hits=" + hits + " engine_target_skipped=" + engine + " los_blocked=" + blocked + " pool=" + pool.size + " budget=" + max_hits + " engine_landed=" + self engine_landed( token ) + " press_to_hit_ms=" + self press_to_hit() );
	return hits;
}

// Everything within r of a point (the gauntlet's fist / its juke position).
function sweep_radius( w, kind, note, center, r, max_hits, token, skip_engine, mult )
{
	if ( !isdefined( mult ) ) mult = 1.0;
	eye = self GetEye();
	fwd = self flat_forward();
	now = GetTime();
	dmg = Int( tod_classes::melee_dmg( w ) * mult );
	pool = util::get_array_of_closest( center, enemies(), undefined, undefined, r + 40 );
	hits = 0;
	engine = 0;
	foreach ( z in pool )
	{
		if ( hits >= max_hits ) break;
		if ( !isdefined( z ) || !IsAlive( z ) ) continue;
		if ( Distance( z.origin + ( 0, 0, 40 ), center ) > r ) continue;
		to = z.origin - self.origin;
		if ( Length( ( to[ 0 ], to[ 1 ], 0 ) ) > 24 && VectorDot( VectorNormalize( ( to[ 0 ], to[ 1 ], 0 ) ), fwd ) < -0.2 ) continue;   // never behind you
		if ( isdefined( z.tod_wm_token ) && z.tod_wm_token == token ) continue;
		if ( skip_engine && isdefined( z.tod_actor_cb_ms ) && now - z.tod_actor_cb_ms <= TOD_WM_ENGINE_WINDOW + TOD_WM_SETTLE * 1000 ) { engine++; continue; }
		if ( !BulletTracePassed( eye, z.origin + ( 0, 0, 40 ), false, self ) ) continue;
		z.tod_wm_token = token;
		self.tod_wm_sweeping = true;
		z DoDamage( dmg, z.origin, self, self, "torso", "MOD_MELEE", 0, w );
		self.tod_wm_sweeping = undefined;
		self hit_tell( kind, z );
		hits++;
	}
	if ( note != "juke" || hits > 0 )
		dev_log( "SWING player=" + self GetEntityNumber() + " kind=" + kind + " note=" + note + " weapon=" + w.name + " dmg=" + dmg + " hits=" + hits + " engine_target_skipped=" + engine + " r=" + r + " pool=" + pool.size + " budget=" + max_hits + " engine_landed=" + self engine_landed( token ) + " press_to_hit_ms=" + self press_to_hit() );
	return hits;
}

// The engine plays the weapon's impact FX and sound on ITS target only; every
// extra target gets the same tell here.
function hit_tell( kind, z )
{
	if ( kind == "sword" ) return;   // blood + the slash read on their own
	fx = ( kind == "punch" ? "dlc5/tomb/fx_one_inch_punch_impact" : "dlc3/stalingrad/fx_dragon_gauntlet_melee_impact" );
	org = z.origin + ( 0, 0, 40 );
	host = Spawn( "script_model", org );
	if ( !isdefined( host ) ) return;   // entity pool full: drop the tell, never throw
	host SetModel( "tag_origin" );
	PlayFXOnTag( fx, host, "tag_origin" );
	host PlaySound( "tod_punch_hit_npc" );
	host thread expire( 1.5 );
}

function expire( seconds )
{
	level endon( "end_game" );
	wait seconds;
	if ( isdefined( self ) ) self Delete();
}

// ---------------------------------------------------------------------------
// The gauntlet's lunge (the engine's melee juke): hits along the path
// ---------------------------------------------------------------------------
function juke_watch()
{
	self endon( "disconnect" );
	self endon( "death" );
	self notify( "tod_wm_juke_watch" );
	self endon( "tod_wm_juke_watch" );
	for ( ;; )
	{
		self waittill( "weapon_melee_juke", w );
		if ( !isdefined( w ) ) w = self GetCurrentWeapon();
		if ( blade_kind( w ) !== "gauntlet" ) continue;
		self juke_sweep( w );
	}
}

function juke_sweep( w )
{
	self endon( "disconnect" );
	self endon( "death" );
	token = GetTime();
	started = token;
	hits = 0;
	ticks = 0;
	start = self.origin;
	dev_log( "JUKE_START player=" + self GetEntityNumber() + " weapon=" + w.name );
	while ( GetTime() - started < TOD_WM_GAUNT_JUKE_MS )
	{
		if ( !( self can_swing() ) || self GetCurrentWeapon() != w ) break;
		self PlayRumbleOnEntity( "damage_light" );
		ahead = self.origin + self GetVelocity() * TOD_WM_GAUNT_JUKE_STEP + ( 0, 0, 40 );
		hits += self sweep_radius( w, "gauntlet", "juke", ahead, TOD_WM_GAUNT_JUKE_R, 1 + self cleave_extra(), token, false );
		ticks++;
		wait TOD_WM_GAUNT_JUKE_STEP;
	}
	dev_log( "JUKE_END player=" + self GetEntityNumber() + " hits=" + hits + " ticks=" + ticks + " travel=" + Distance2D( start, self.origin ) );
}

// ---------------------------------------------------------------------------
// The fling: an ordinary zombie a Warrior blade kills is thrown, the stock punch's
// and gauntlet's own launch. Elites own their deaths.
// ---------------------------------------------------------------------------
function on_zombie_death( attacker )
{
	if ( !isdefined( self ) || !isdefined( attacker ) || !IsPlayer( attacker ) ) return;
	if ( isdefined( level.tod_gs_charge_fn ) ) attacker [[ level.tod_gs_charge_fn ]]( self );   // _tod_class_kit gs_charge
	kind = blade_kind( self.damageweapon );
	if ( !isdefined( kind ) ) return;
	if ( !isdefined( self.damagemod ) || !IsSubStr( self.damagemod, "MELEE" ) ) return;
	if ( is_elite( self ) || IS_TRUE( self.tod_bat_launched ) ) return;
	if ( isdefined( level.ragdoll_limit_check ) && ![[ level.ragdoll_limit_check ]]() ) return;
	to = self.origin - attacker.origin;
	dir = VectorNormalize( ( to[ 0 ], to[ 1 ], 0 ) );
	if ( kind == "punch" ) impulse = dir * RandomIntRange( 125, 150 ) + ( 0, 0, RandomIntRange( 75, 150 ) );   // stock zombie_punch_death
	else if ( kind == "gauntlet" ) impulse = dir * RandomIntRange( 140, 170 ) + ( 0, 0, RandomIntRange( 90, 120 ) );
	else impulse = dir * RandomIntRange( 90, 120 ) + ( 0, 0, RandomIntRange( 50, 80 ) );
	self.tod_bat_launched = true;   // the shared once-per-body mark (the bat's)
	self StartRagdoll();
	self LaunchRagdoll( impulse );
	dev_log( "FLING ent=" + self GetEntityNumber() + " player=" + attacker GetEntityNumber() + " kind=" + kind + " impulse=" + impulse );
}

// ---------------------------------------------------------------------------
// THE GAUNTLET'S RIGHT-LEFT HOOK: the hand is the form in hand (the left-hand twin
// "<form>_l"); hook_advance() logs the chain once per weapon_melee.
// ---------------------------------------------------------------------------
function hook_advance( w )
{
	now = GetTime();
	dt = ( isdefined( self.tod_wm_hook_ms ) ? now - self.tod_wm_hook_ms : -1 );
	if ( dt < 0 || dt > TOD_WM_ALT_IDLE_MS ) self.tod_wm_hook_n = 0;   // a gap: a new chain
	side = ( alt_is_left( w ) ? "L" : "R" );
	same = ( isdefined( self.tod_wm_hook_last ) && dt >= 0 && dt <= TOD_WM_ALT_IDLE_MS && side == self.tod_wm_hook_last );
	self.tod_wm_hook_n = ( isdefined( self.tod_wm_hook_n ) ? self.tod_wm_hook_n : 0 ) + 1;
	self.tod_wm_hook_last = side;
	self.tod_wm_hook_ms = now;
	self.tod_wm_press_pending_ms = undefined;   // this press was answered
	dev_log( "SWING n=" + self.tod_wm_hook_n + " dt_ms=" + dt + " hand=" + side + ( same ? " SAME_HAND_TWICE" : "" ) + " form=" + w.name + " press_to_swing_ms=" + self press_to_hit() + " player=" + self GetEntityNumber() );
	return side;
}

// A gauntlet form's name, less the engine's trailing "_zm" if it kept it.
function alt_base_name( w )
{
	if ( !isdefined( w ) || !isdefined( w.name ) ) return "";
	n = w.name;
	if ( n.size > 3 && GetSubStr( n, n.size - 3, n.size ) == "_zm" ) n = GetSubStr( n, 0, n.size - 3 );
	return n;
}

function alt_is_left( w )
{
	n = alt_base_name( w );
	if ( n.size < 3 || !IsSubStr( n, "cc_gauntlet" ) ) return false;
	return ( GetSubStr( n, n.size - 2, n.size ) == "_l" );
}

// The other hand's twin of a gauntlet form, or undefined (not linked).
function alt_other( w )
{
	n = alt_base_name( w );
	if ( n == "" || !IsSubStr( n, "cc_gauntlet" ) ) return undefined;
	if ( alt_is_left( w ) ) return tod_classes::weapon_or_zm( GetSubStr( n, 0, n.size - 2 ) );
	return tod_classes::weapon_or_zm( n + "_l" );
}

// Hand `from` (in hand) over to `to`: _tod_upgrades swap_primary's proven order - GIVE
// (with the camo the pack earned), switch and verify, TAKE last. Both hands raise on the
// idle in 0.05 s, so nothing shows. reconcile_twin leaves a "<rung>_l" alone, so no
// swap latch is needed.
function alt_swap( from, to, why )
{
	t0 = GetTime();
	before = self alt_primaries();
	if ( !( self HasWeapon( to ) ) ) self GiveWeapon( to, tod_classes::pap_camo_options( self, to ) );
	self ShouldDoInitialWeaponRaise( to, false );
	held = ( self GetCurrentWeapon() == from );
	if ( held )
	{
		for ( i = 0; i < 10; i++ )
		{
			self SwitchToWeaponImmediate( to );
			if ( self GetCurrentWeapon() == to ) break;
			wait 0.05;
			if ( !isdefined( self ) ) return false;
			if ( self laststand::player_is_in_laststand() ) break;
		}
	}
	ok = ( !held || self GetCurrentWeapon() == to );
	if ( ok && self HasWeapon( from ) ) self TakeWeapon( from );
	else if ( !ok && self HasWeapon( to ) && self GetCurrentWeapon() != to ) self TakeWeapon( to );   // the switch never took: keep the hand they hold
	if ( ok ) self.tod_wm_alt_swap_ms = GetTime();
	dev_log( "ALT_SWAP player=" + self GetEntityNumber() + " why=" + why + " from=" + from.name + " to=" + to.name + " held=" + held + " ok=" + ok + " swap_ms=" + ( GetTime() - t0 ) + " primaries_before=" + before + " primaries_after=" + self alt_primaries() );
	return ok;
}

// The primaries by name, "[a,b,c]" (give-before-take briefly holds one more: with
// tod_dev_all_guns a Warrior holds punch + gauntlet + sword + the twin = 4. Nothing
// stock takes one in that frame: player_too_many_weapons_monitor is OFF in
// zm_tod2_cybercity.gsc and get_player_weapon_limit is read only by buys; the log
// shows any drop anyway.)
function alt_primaries()
{
	s = "";
	foreach ( p in self GetWeaponsListPrimaries() )
	{
		if ( s != "" ) s += ",";
		s += p.name;
	}
	return "[" + s + "]";
}

// The left twin -> the right hand while something else is in hand (a Bash proxy, a
// perk bottle): give the right, take the left. Returns the right-hand weapon.
function alt_holster_right( l, why )
{
	r = alt_other( l );
	if ( !isdefined( r ) ) return l;
	if ( !( self HasWeapon( r ) ) ) self GiveWeapon( r, tod_classes::pap_camo_options( self, r ) );
	self ShouldDoInitialWeaponRaise( r, false );
	if ( self HasWeapon( l ) ) self TakeWeapon( l );
	dev_log( "ALT_REVERT player=" + self GetEntityNumber() + " why=holster_" + why + " from=" + l.name + " to=" + r.name + " primaries_after=" + self alt_primaries() );
	return r;
}

// level.tod_wm_alt_right_fn (_tod_class_kit bash_run, once the proxy is in hand): the
// weapon a Bash hands back to - the right hand, never the left twin (the lead's rule).
function alt_right_for( previous )
{
	if ( !alt_is_left( previous ) ) return previous;
	if ( self GetCurrentWeapon() == previous ) return previous;   // never take the weapon in hand
	return self alt_holster_right( previous, "bash" );
}

// After a gauntlet swing: wait for the clip to finish (IsMeleeing, capped at the clip's
// length), then swap to the other hand. The newest swing owns the swap.
function alt_after_swing( w )
{
	self endon( "disconnect" );
	self endon( "death" );
	self notify( "tod_wm_alt_swing" );
	self endon( "tod_wm_alt_swing" );
	self alt_block( false, "new_swing" );   // a block an older swing left behind
	t0 = GetTime();
	cap = Int( 600 * swing_scale( w ) );   // gen_tod_twins cc_gauntlet meleeTime 0.6 x the MELEE SPEED step
	block_at = cap - TOD_WM_ALT_BLOCK_LEAD_MS;
	seen = false;
	ended = "cap";
	while ( GetTime() - t0 < cap + 150 )
	{
		// the clip's last server frame: nothing may start on this hand again
		if ( GetTime() - t0 >= block_at && self GetCurrentWeapon() == w ) self alt_block( true, "clip_end" );
		if ( self IsMeleeing() ) seen = true;
		else if ( seen ) { ended = "meleeing_off"; break; }
		else if ( GetTime() - t0 >= cap ) break;
		wait 0.05;
	}
	cur = self GetCurrentWeapon();
	if ( cur != w || !( self can_swing() ) )
	{
		self alt_block( false, "skip" );
		dev_log( "ALT_SKIP player=" + self GetEntityNumber() + " form=" + w.name + " reason=" + ( self can_swing() ? "weapon_changed" : "down_or_dead" ) + " wait_ms=" + ( GetTime() - t0 ) );
		return;
	}
	other = alt_other( w );
	if ( !isdefined( other ) )
	{
		self alt_block( false, "skip" );
		dev_log( "ALT_SKIP player=" + self GetEntityNumber() + " form=" + w.name + " reason=twin_not_linked" );
		return;
	}
	dev_log( "ALT_WAIT player=" + self GetEntityNumber() + " form=" + w.name + " wait_ms=" + ( GetTime() - t0 ) + " ended=" + ended + " cap_ms=" + cap );
	ok = self alt_swap( w, other, ( alt_is_left( w ) ? "after_left" : "after_right" ) );
	self alt_block( false, "swapped ok=" + ok );
	if ( ok && alt_is_left( other ) ) self thread alt_idle_revert( other );
}

// The swap window (STRICT RIGHT-LEFT above): fire and melee are held off from the clip's
// last frame until the other hand is in hand, so the next swing can only start on it.
// Bash and Gravity Smash hold the same two locks while they run and restore them
// themselves at their end, so a release during one of them leaves theirs alone.
function alt_block( on, why )
{
	if ( on )
	{
		if ( isdefined( self.tod_wm_alt_block_ms ) ) return;
		self.tod_wm_alt_block_ms = GetTime();
		self DisableWeaponFire();
		self AllowMelee( false );
		dev_log( "ALT_BLOCK player=" + self GetEntityNumber() + " why=" + why + " form=" + self GetCurrentWeapon().name + " meleeing=" + self IsMeleeing() );
		return;
	}
	if ( !isdefined( self.tod_wm_alt_block_ms ) ) return;
	held = GetTime() - self.tod_wm_alt_block_ms;
	self.tod_wm_alt_block_ms = undefined;
	restored = !( IS_TRUE( self.tod_bash_busy ) || IS_TRUE( self.tod_gs_busy ) );
	if ( restored )
	{
		self EnableWeaponFire();
		self AllowMelee( true );
	}
	dev_log( "ALT_UNBLOCK player=" + self GetEntityNumber() + " why=" + why + " held_ms=" + held + " restored=" + restored + " form=" + self GetCurrentWeapon().name );
}

// The left twin in hand and no punch: the right hand comes back after
// TOD_WM_ALT_IDLE_MS, at once on USE (a PaP / door / altar is bought with the right),
// or in the holster when something else is drawn (a Bash proxy, a perk bottle).
function alt_idle_revert( l )
{
	self endon( "disconnect" );
	self endon( "death" );
	self endon( "tod_wm_alt_swing" );   // a left punch: alt_after_swing takes it from here
	t0 = GetTime();
	for ( ;; )
	{
		self.tod_wm_alt_idle_seen = GetTime();
		wait 0.05;
		if ( self laststand::player_is_in_laststand() ) return;   // the engine owns the weapons; alt_input_tick catches the left twin after
		cur = self GetCurrentWeapon();
		if ( cur == level.weaponNone ) continue;   // mid-switch
		if ( cur != l )
		{
			if ( self HasWeapon( l ) ) self alt_holster_right( l, "drawn cur=" + cur.name );
			return;
		}
		why = undefined;
		if ( GetTime() - t0 >= TOD_WM_ALT_IDLE_MS ) why = "idle";
		else if ( self UseButtonPressed() ) why = "use";
		if ( isdefined( why ) )
		{
			r = alt_other( l );
			if ( isdefined( r ) ) self alt_swap( l, r, why );
			return;
		}
	}
}

// input_watch, every tick a gauntlet is in hand: a press nothing answered is logged,
// and a left twin nobody is watching (after a revive restored it) is handed back.
function alt_input_tick()
{
	if ( isdefined( self.tod_wm_press_pending_ms ) && GetTime() - self.tod_wm_press_pending_ms > TOD_WM_ALT_DROP_MS )
	{
		dev_log( "PRESS_DROPPED player=" + self GetEntityNumber() + " form=" + self GetCurrentWeapon().name + " pressed_ms_ago=" + ( GetTime() - self.tod_wm_press_pending_ms ) + " last_swap_ms_ago=" + ( isdefined( self.tod_wm_alt_swap_ms ) ? GetTime() - self.tod_wm_alt_swap_ms : -1 ) + " meleeing=" + self IsMeleeing() );
		self.tod_wm_press_pending_ms = undefined;
	}
	if ( !TOD_GAUNTLET_ALT_TWINS ) return;
	cur = self GetCurrentWeapon();
	if ( !alt_is_left( cur ) ) return;
	if ( isdefined( self.tod_wm_alt_idle_seen ) && GetTime() - self.tod_wm_alt_idle_seen < 250 ) return;   // alt_idle_revert has it
	if ( isdefined( self.tod_wm_hook_ms ) && GetTime() - self.tod_wm_hook_ms < TOD_WM_ALT_IDLE_MS ) return;   // mid-chain (alt_after_swing has it)
	dev_log( "ALT_ORPHAN player=" + self GetEntityNumber() + " form=" + cur.name + " (a revive / regive restored the left twin)" );
	self thread alt_idle_revert( cur );
}

// level.tod_wm_hit_mult_fn (_tod_upgrades upgrade_damage_cb): the engine's own
// gauntlet hit on the left hand lands x TOD_WM_HOOK_LEFT_MULT. Our crowd sweep
// (tod_wm_sweeping) already carries its side, so it passes through at 1.0.
function hook_mult( attacker, weapon, meansofdeath )
{
	if ( !isdefined( attacker ) || !IsPlayer( attacker ) ) return 1.0;
	if ( !isdefined( meansofdeath ) || meansofdeath != "MOD_MELEE" ) return 1.0;
	if ( blade_kind( weapon ) !== "gauntlet" ) return 1.0;
	if ( IS_TRUE( attacker.tod_wm_sweeping ) ) return 1.0;
	if ( IS_TRUE( attacker.tod_bash_busy ) ) return 1.0;   // BASH hits name the blade too; they are not a hook (a gauntlet Bash landed x0.75 whenever the next hook was the left)
	if ( !alt_is_left( weapon ) ) return 1.0;   // the left-hand twin IS the left hook
	return TOD_WM_HOOK_LEFT_MULT;
}

// ---------------------------------------------------------------------------
// THE SWORD'S HIT SOUND (Hellbound's on_caliburn_melee_hit): every sword melee
// contact, lethal or not, at the contact point, at most once per victim per
// 100 ms. self = the damaged actor; stock threads this per damage event.
// ---------------------------------------------------------------------------
function on_actor_hit( willBeKilled, inflictor, attacker, damage, flags, meansofdeath, weapon, vpoint, vdir, sHitLoc, psOffsetTime, boneIndex, surfaceType )
{
	if ( !isdefined( self ) || !isdefined( attacker ) || !IsPlayer( attacker ) ) return;
	if ( !isdefined( damage ) || damage <= 0 ) return;
	if ( !isdefined( meansofdeath ) || meansofdeath != "MOD_MELEE" ) return;
	// the ENGINE's own blade hit (never our sweeps' DoDamage): MELEE RANGE's whiff test (reach_bonus)
	if ( isdefined( blade_kind( weapon ) ) && !IS_TRUE( attacker.tod_wm_sweeping ) ) attacker.tod_wm_engine_hit_ms = GetTime();
	if ( blade_kind( weapon ) !== "sword" ) return;
	if ( isdefined( self.tod_wm_hit_sound_ms ) && GetTime() - self.tod_wm_hit_sound_ms <= 100 ) return;
	self.tod_wm_hit_sound_ms = GetTime();
	org = ( isdefined( vpoint ) ? vpoint : self.origin + ( 0, 0, 40 ) );
	e = Spawn( "script_origin", org );   // the proven lane for a custom 3D alias (CLAUDE.md v19.21c)
	if ( !isdefined( e ) ) return;
	e PlaySound( TOD_WM_SWORD_HIT_SOUND );
	e thread expire( 2 );
	if ( level.tod_wm_hit_logs < 20 )
	{
		level.tod_wm_hit_logs++;
		dev_log( "SWORD_HIT_SOUND victim=" + self GetEntityNumber() + " player=" + attacker GetEntityNumber() + " killed=" + IS_TRUE( willBeKilled ) + " alias=" + TOD_WM_SWORD_HIT_SOUND );
	}
}

