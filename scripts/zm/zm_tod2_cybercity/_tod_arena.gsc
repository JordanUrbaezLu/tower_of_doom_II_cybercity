// THE BATTLE ARENA (docs/185, user 2026-09-27).
//
// "floor 40 ... some kind of teleporting chamber that everyone can go in and it
// can be activated on the inside ... you'll be teleported off into a battle
// arena ... rounds of enemies and they will get stronger ... level one ... all
// the way to level 10 ... a little bit of randomization, so one round might be
// zombies and manglers ... one set where maybe it's doppelgas and amalgam ...
// the only difference is that on each level that round might have more health,
// stronger hits ... when you succeed everyone will get a card and then you'll
// be sent back to the tower" + "it will cost 500 per teleport and it will go to
// the new teleporter bay at the top of tower".
//
// The user's calls (2026-09-27): ONE LEVEL PER TRIP (trip 1 = level 1 ... 10);
// a WIPE IS GAME OVER (no special case: stock ends the game); EVERY LIVING
// PLAYER must be inside the chamber to start it; floor 40 carries only the
// chamber (its transit pad is gone). Since docs/202 v2 (THE HEART) the chamber
// is floor 40's haven field: the gate stands at the field's centre and "inside"
// is the field (tod_arena_data::chamber_r). The Amalgam is not in the map yet — the
// enemy sets use the horde, the Mangler and the Doppelghast (add a set row
// when it lands).
//
// v2 THE CRUCIBLE (docs/185 v2, user 2026-10-03: "the battle arena teleporter
// waits way too long to actually teleport please fix the latency. It doesnt line
// up. Also the battle arena needs to be actually designed ... no real spot to
// camp ... heights to allow vertical traversal ... play into the characters for
// skill gap but be super hard as well so spawns need to be thought out"):
//   * THE JUMP LINES UP. The charge effect, its sound and the banner start in the
//     frame the gate is used; the party jumps TOD_ARENA_CHARGE_SECS later (the
//     transit pads' own 0.8 s); the departure flash fires in the jump frame and
//     the arrival flash two frames after it. v1 called fx_burst INLINE three
//     times — it waits out its whole effect lifetime — so the user's 2026-10-01
//     log reads: press 482.9 s, sound 486.5 s (after the effect had ended), jump
//     489.5 s, arrival flash 492.65 s (3.15 s after landing). The return had the
//     same fault (a 1.3 s inline charge, a dead 0.8 s, a 3.1 s-late arrival).
//   * THE ROOM is three levels (tools/battle_arena_layout.js): the pit, the ring,
//     four rising spokes and the dais the party lands on. Every level is on foot.
//   * THE DIRECTOR picks every spawn: never within TOD_ARENA_SPAWN_MIN of anyone,
//     arriving soon (a distance band), from where the party is not looking, spread
//     away from the zombies already up, and — when a player stays inside
//     TOD_ARENA_CAMP_R for TOD_ARENA_CAMP_MS — pulled toward that player (and the
//     next elite comes through the gate nearest them). Its core is PURE
//     (best_spot / spot_score / elite_gate): tools/test_battle_arena.js runs it.
//   * THE DAIS OVERCHARGES while a fight runs: a 2.5 s wind-up (the teleporter's
//     own charge), then a discharge that takes TOD_ARENA_PURGE_PCT of the health
//     of everyone still on it and kills the zombies on it. The one spot four
//     players could hold is a spot they must keep leaving — and a skilled party
//     lures the horde onto it.
//   * NO FALL DAMAGE in the arena: every ledge is open on purpose.
//   * HARDER: more zombies, full sprint from level 1, elites from wave 1 on level 3+.
//
// v2.1 THE READABLE FIGHT (docs/185 v2.1, user 2026-10-03: "Give the arena one more
// pass from a players perspective"):
//   * THE READOUT (TodArena.lua, the zero-bit tod_arena event): LEVEL l OF 10 / WAVE w
//     OF n / N LEFT at the top of the screen for the whole fight; the count ticks on every
//     kill, turns hot at TOD_ARENA_HUD_HOT, reads WAVE CLEARED / LEVEL CLEARED / THE
//     DEALER; re-sent every TOD_ARENA_HUD_RESEND_MS (a rebuilt HUD hydrates; the
//     widget ignores a re-send that changes nothing).
//   * THE CUES (tools/battle_arena/make_sounds.py, generated): a horn as a wave
//     begins, a sting as one is cleared, a fanfare as the level is, all 2D to every
//     player; and THE GATE: an elite's gate charges (the teleporter's wind-up + its
//     own 3D cue, TOD_ARENA_GATE_TELL_SECS) and flashes before the elite rises in it,
//     so the room says WHERE the threat comes from before it does.
//   * THE MOOD LIGHTS: a glow host over each pylon collar and one over the dais
//     (GENERATED arena_mood_orgs) on the todPerkGlow lane, coloured by level
//     (mood_index: teal -> yellow -> orange -> red); the dais light goes WHITE for
//     the overcharge's wind-up, so the warning is visible from the whole room.
//   * THE OVERCHARGE WARNS EVERYONE WHO STEPS ON during its wind-up, not only
//     those on the dais as it starts; THE CHAMBER tells a player the level before
//     they commit (once per level, after the haven's own SAFE ZONE label).
//
// FLOW. chamber_think: one trigger_radius_use on the floor-40 gate (the field's
// centre, docs/202 v2). A use = every playing player inside -> arena_run: charge
// -> hold the tower (stock spawning off, leftover horde deleted and refunded) ->
// enable arena_zone -> the party lands on the dais -> TOD_ARENA_WAVES waves of the
// level's set, each one killed to the last -> win: revive the downed, freeze the
// world, deal every player a card (run_upgrade_event), then send everyone to the
// top bay and give the tower back.
//
// WHAT ELSE READS THIS. level.tod_arena_dmg_mult (_tod_bosses::boss_player_damage
// — "stronger hits"); level.tod_trial_box, which this module sets to the arena
// room while a fight runs, is what holds the normal-round Mangler/Doppelghast
// director (_tod_cyber_elites::hold_reason) and keeps every elite relocation
// (_tod_bosses::pick_spawn_point) inside the room. This module is its only
// writer (the field keeps an older name from a retired mode). level.tod_arena_active
// (true from the jump in to the return) is read by _tod_ambush, _tod_lucky and the
// fall guard below.
//
// THE DEALER'S HOUSE (docs/207, 2026-10-04, user: "a separate arena that is even better and slightly
// bigger ... the one players will get sent to on battle arena wave 10. The final fight"): the LAST
// level is _tod_house::run - the Black Market parlour, the cut scene, the rigged last roll, the
// drain to one health under his dome and the Dealer's two-state fight - in place of the waves.
// arena_run branches after hold_tower; arena_win rides home from level.tod_arena_depart (the
// house's dais). The readout gets two flags (HOUSE / DEALER). (THE KEEPER, docs/186, was level
// 10's boss wave before the house; his wave, the TOD_ARENA_HOUSE toggle back to him and his
// readout flag retired whole 2026-10-05.)
//
// Logs: [TOD_ARENA] (dev), every decision and outcome with its reason.

#using scripts\shared\array_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;
#using scripts\shared\ai\zombie_utility;
#using scripts\zm\_zm_laststand;
#using scripts\zm\_zm_score;
#using scripts\zm\_zm_utility;
#using scripts\zm\_zm_zonemgr;
#using scripts\zm\zm_tod2_cybercity\_tod_arena_data;
#using scripts\zm\zm_tod2_cybercity\_tod_teleport;      // pad model, beam, charge/flash FX (proven recipe)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;  // play_sound_at_origin (the proven 3D lane)
#using scripts\zm\zm_tod2_cybercity\_tod_upgrades;      // set_world_pause + run_upgrade_event (the card deal)
#using scripts\zm\zm_tod2_cybercity\_tod_mangler;       // spawn_at
#using scripts\zm\zm_tod2_cybercity\_tod_doppelghast;   // spawn_hunter
#using scripts\zm\zm_tod2_cybercity\_tod_atmosphere;    // arena_music_start/end (the boss track, 115)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_lights;   // set_glow: the todPerkGlow client light lane (THE MOOD LIGHTS, v2.1)
#using scripts\zm\zm_tod2_cybercity\_tod_house;         // THE DEALER'S HOUSE (docs/207): level 10 is his two rooms
#using scripts\zm\zm_tod2_cybercity\_tod_house_data;    // GENERATED: in_house (the fall guard covers his arena too)

#insert scripts\shared\shared.gsh;
#insert scripts\zm\zm_tod2_cybercity\_tod_tester.gsh;   // TOD_TESTER_KIT: the test start level (docs/207)

#precache( "eventstring", "tod_arena" );   // THE READOUT (TodArena.lua, v2.1)

#namespace tod_arena;

// ---- knobs (one per symptom) ------------------------------------------------
#define TOD_ARENA_COST          0      // FREE since 2026-09-28 (user: "The battle arena teleporter is free"; was 500, paid by the player who starts it)
#define TOD_ARENA_LEVELS        10
#define TOD_ARENA_WAVES         3      // waves per level; each is killed to the last enemy
#define TOD_ARENA_CHARGE_SECS   0.8    // the gate's charge before the jump. LOCKSTEP _tod_teleport.gsc TOD_TP_CHARGE_SEC (tools/test_battle_arena.js): the same beat as every pad (v1: 3.0 s plus 3.6 s of inline effect waits)
#define TOD_ARENA_RETURN_SECS   0.8    // the dais's charge before the ride home (v1: 1.3 s inline + 0.8 s)
#define TOD_ARENA_LAND_SECS     3.0    // breath after landing before wave 1 (from the landing now; v1 ran it after a 3.15 s inline effect)
#define TOD_ARENA_WAVE_GAP      3.0    // breath between waves (v1: 4.0)
#define TOD_ARENA_HP_STEP       0.25   // enemy health x(1 + step*(level-1)): Lv10 = x3.25
#define TOD_ARENA_DMG_STEP      0.15   // enemy hits  x(1 + step*(level-1)): Lv10 = x2.35
// STATIC DIFFICULTY BY LEVEL (2026-10-04, docs/210; the user's own description, 2026-10-03: "rounds dont count in
// there and its a static difficulty of progression through the battle arena levels"). Arena health used to be the
// TOWER round's zombie health at the moment of entry x hp_mult, so the same level was ~2x harder entered ten rounds
// later (L9 at round 30: 1890 per zombie) and the Dealer's 60 units ran away with the round. Now every arena fight
// reads ONE fixed round per level: hp_round( lvl ) = BASE + STEP x (level - 1) (L1 round 10 ... L9 round 26, the
// Dealer round 28), published as level.tod_arena_hp_round, which _tod_power_scale::track_rounds holds
// level.zombie_health on while it is set - so ordinary zombies, elites, the Dealer and every ability that hits in
// round-zombie units agree. Cleared on the win and on the abort. hp_mult and dmg_mult still apply on top.
#define TOD_ARENA_HP_ROUND_BASE 10     // level 1 fights at round 10's health (94 per zombie)
#define TOD_ARENA_HP_ROUND_STEP 2      // + 2 rounds per level: L5 round 18, L9 round 26, the Dealer round 28
#define TOD_ARENA_ZOMBIES_BASE  12     // ordinary zombies per wave at level 1, solo (v1: 6)
#define TOD_ARENA_ZOMBIES_LV    3      // + per level (v1: 2): Lv10 solo = 39 a wave before the set's factor
#define TOD_ARENA_ZOMBIES_COOP  0.5    // x(1 + this*(players-1))
#define TOD_ARENA_ELITE_UNITS   5      // an arena elite's HP in round zombies (the live Mangler/Doppel figure) before the level multiplier
#define TOD_ARENA_ELITE_EVERY   3      // a set's elites: 1, +1 every this many levels (v1: 4)
#define TOD_ARENA_QUIET_LEVELS  2      // levels whose FIRST wave is the horde alone (v1: 3)
#define TOD_ARENA_SPAWN_GAP     0.25   // seconds between ordinary spawns (v1: 0.35); the live cap still rules
#define TOD_ARENA_SPRINT_ROUND  18     // arena zombies run at least this round's speed = full sprint. LOCKSTEP _tod_zombie_speed.gsc TOD_ZSPEED_FULL_ROUND
#define TOD_ARENA_ENTER_Z       40     // "inside the chamber": floor-40 .. floor+CHAMBER_H
#define TOD_ARENA_RING          48     // top-bay arrival fan-out (the transit ring)
#define TOD_ARENA_STALL_MS      60000  // no kill for this long -> stuck ordinary zombies are removed (never trap the party)
// THE DIRECTOR (docs/185 v2). best_spot() scores every spawn point each spawn:
#define TOD_ARENA_SPAWN_MIN     380    // never closer than this to any player (3D): no zombie rises in your face
#define TOD_ARENA_SPAWN_IDEAL   650    // the distance it likes best: on you in seconds, not instantly
#define TOD_ARENA_SPAWN_BAND    100    // -1 point per this many units away from the ideal
#define TOD_ARENA_SPAWN_SEEN_DOT 0.5   // a spot inside ~60 degrees of a player's view counts as seen
#define TOD_ARENA_SPAWN_UNSEEN  1.5    // + this x the share of the party NOT looking at it (they come from behind)
#define TOD_ARENA_SPREAD_R      400    // zombies already up within this of a spot ...
#define TOD_ARENA_SPREAD_COST   0.4    // ... cost this much each (the horde comes from every side)
#define TOD_ARENA_REPEAT_COST   2.0    // the spot used last time
#define TOD_ARENA_SPAWN_JITTER  1.0    // a random 0..this on every score
#define TOD_ARENA_CAMP_R        200    // a player who stays inside this circle ...
#define TOD_ARENA_CAMP_MS       7000   // ... this long is CAMPING
#define TOD_ARENA_CAMP_REACH    1100   // spots within this of a camper ...
#define TOD_ARENA_CAMP_PULL     3.0    // ... gain up to this much (the nearest the most); the next elite takes the gate nearest them
#define TOD_ARENA_GATE_MEMORY   3      // an elite will not reuse any of the last this-many gates if another is legal
// THE DAIS OVERCHARGE (docs/185 v2)
#define TOD_ARENA_PURGE         1      // 0 = the dais never discharges
#define TOD_ARENA_PURGE_FIRST   20     // seconds after wave 1 starts
#define TOD_ARENA_PURGE_EVERY   25     // seconds from one discharge to the next
#define TOD_ARENA_PURGE_WARN    2.5    // the wind-up (charge effect + sound) before it fires
#define TOD_ARENA_PURGE_PCT     0.40   // of a player's max health, for everyone still on the dais
#define TOD_ARENA_PURGE_ELITE_PCT 0.15 // of an elite's max health (ordinary zombies die)
// THE TESTER KIT (docs/207): with TOD_TESTER_KIT on, the arena opens AT this level, so a tester's first
// trip is the final fight (1 = level 1 as ever). It goes away with the kit (a release build warns on the kit).
#define TOD_ARENA_TEST_START_LEVEL   10

// constant hints ONLY (the triggerstring budget: lint_tod_hints counts these)
// ---- v2.1 THE READABLE FIGHT (docs/185 v2.1) ------------------------------
#define TOD_ARENA_HUD_RESEND_MS   2000   // the readout's state is re-sent this often (a rebuilt HUD hydrates; a re-send that changes nothing draws nothing)
#define TOD_ARENA_HUD_HOT         3      // this many enemies left or fewer: the count turns hot (hunt them). LOCKSTEP TodArena.lua HOT
#define TOD_ARENA_HUD_WAVE        1      // flags (LOCKSTEP TodArena.lua FLAG_*): a wave just began
#define TOD_ARENA_HUD_CLEARED     2      // the wave was just cleared
// (4 was TOD_ARENA_HUD_BOSS, THE KEEPER lives: retired with him 2026-10-05; LOCKSTEP TodArena.lua)
#define TOD_ARENA_HUD_LEVEL       8      // the level is cleared
#define TOD_ARENA_HUD_HOUSE       16     // THE DEALER'S HOUSE (docs/207): the wave line reads THE FINAL FIGHT
#define TOD_ARENA_HUD_DEALER      32     // THE DEALER lives (the count line names him)
#define TOD_ARENA_GATE_TELL_SECS  1.0    // a gate charges (effect + cue) this long before its elite rises
#define TOD_ARENA_MOOD            1      // 0 = no level mood lights
#define TOD_ARENA_MOOD_WARN_IDX   8      // the dais light during the overcharge's wind-up (white)
#define TOD_ARENA_NOTICE_MS       2000   // a player inside the chamber this long is told the level (after the haven's SAFE ZONE label)
#define TOD_ARENA_SND_WAVE   "tod_arena_wave"    // 2D, every player: a wave begins (the horn)
#define TOD_ARENA_SND_CLEAR  "tod_arena_clear"   // 2D: a wave is cleared (never the level's last: the fanfare takes that)
#define TOD_ARENA_SND_LEVEL  "tod_arena_level"   // 2D: the level is cleared
#define TOD_ARENA_SND_GATE   "tod_arena_gate"    // 3D at the gate: it opens

#define TOD_ARENA_HINT_READY    "Hold ^3[{+activate}]^7 ^5BATTLE ARENA^7 - enter the arena - ^2FREE"
#define TOD_ARENA_HINT_GUARDIANS "^5BATTLE ARENA^7 - ^1defeat the guardians"   // docs/202 v3: the haven's guardians still live
#define TOD_ARENA_HINT_POWER    "^5BATTLE ARENA^7 - ^1power required"
#define TOD_ARENA_HINT_DONE     "^5BATTLE ARENA^7 - ^2conquered"

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_ARENA] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// ---------------------------------------------------------------------------
// ENEMY SETS. One is drawn per trip (never the same twice running). Per wave:
// zombies = base count x zf; manglers/doppels = the row's own ladder. The
// level changes only the numbers and the health/damage multipliers.
// ---------------------------------------------------------------------------
function register_sets()
{
	level.tod_arena_sets = [];
	add_set( "zombies and manglers",     1.0, "mangler" );
	add_set( "zombies and doppelghasts", 1.0, "doppel" );
	add_set( "the hunters",              0.5, "both" );
	add_set( "the horde",                1.6, "none" );
}

function add_set( name, zf, elites )
{
	s = SpawnStruct();
	s.name = name;
	s.zf = zf;
	s.elites = elites;
	level.tod_arena_sets[ level.tod_arena_sets.size ] = s;
}

function pick_set()
{
	n = level.tod_arena_sets.size;
	i = RandomInt( n );
	if ( n > 1 && isdefined( level.tod_arena_last_set ) && i == level.tod_arena_last_set )
		i = ( i + 1 + RandomInt( n - 1 ) ) % n;
	level.tod_arena_last_set = i;
	return level.tod_arena_sets[ i ];
}

function hp_mult( lvl )  { return 1.0 + TOD_ARENA_HP_STEP * ( lvl - 1 ); }
function hp_round( lvl ) { return TOD_ARENA_HP_ROUND_BASE + TOD_ARENA_HP_ROUND_STEP * ( lvl - 1 ); }   // the static health round (above)
function dmg_mult( lvl ) { return 1.0 + TOD_ARENA_DMG_STEP * ( lvl - 1 ); }

// PURE. Elites of each kind in wave w of level lvl. The first TOD_ARENA_QUIET_LEVELS
// levels open with a horde-only wave; a set's elites climb one every
// TOD_ARENA_ELITE_EVERY levels ("the hunters": one of each, +1 every four).
function elite_count( set, kind, lvl, w )
{
	if ( w == 1 && lvl <= TOD_ARENA_QUIET_LEVELS )
		return 0;
	if ( set.elites == "none" )
		return 0;
	if ( set.elites == "both" )
		return 1 + int( ( lvl - 1 ) / 4 );
	if ( set.elites == kind )
		return 1 + int( ( lvl - 1 ) / TOD_ARENA_ELITE_EVERY );
	return 0;
}

// PURE: ordinary zombies per wave for a party of np.
function zombie_count_for( set, lvl, np )
{
	if ( np < 1 )
		np = 1;
	n = ( TOD_ARENA_ZOMBIES_BASE + TOD_ARENA_ZOMBIES_LV * ( lvl - 1 ) ) * set.zf * ( 1 + TOD_ARENA_ZOMBIES_COOP * ( np - 1 ) );
	return int( n + 0.5 );
}

function zombie_count( set, lvl )
{
	return zombie_count_for( set, lvl, playing_players().size );
}

// ---------------------------------------------------------------------------
// INIT
// ---------------------------------------------------------------------------
function init()
{
	level.tod_arena_level = 1;
	level.tod_arena_busy = false;
	level.tod_arena_ai = [];
	register_sets();
	level.tod_arena_hud_push_fn = &hud_push;     // THE DEALER'S HOUSE (docs/207) drives the readout through these two
	level.tod_arena_hud_watch_fn = &hud_watch;
	tod_house::init();
	if ( TOD_TESTER_KIT && TOD_ARENA_TEST_START_LEVEL > 1 )
	{
		level.tod_arena_level = TOD_ARENA_TEST_START_LEVEL;
		dev_log( "TEST_START_LEVEL level=" + level.tod_arena_level + " (TOD_TESTER_KIT: the first trip is the final fight)" );
	}
	// NO FALL DAMAGE IN THE ARENA (docs/185 v2): every ledge is open on purpose
	// (the doors' broken-drop guard is the precedent for the lane)
	if ( !isdefined( level.player_damage_callbacks ) ) level.player_damage_callbacks = [];
	ArrayInsert( level.player_damage_callbacks, &arena_fall_guard, 0 );
	level thread chamber_think();
}

function playing_players()
{
	out = [];
	foreach ( p in GetPlayers() )
		if ( isdefined( p ) && p.sessionstate == "playing" )
			out[ out.size ] = p;
	return out;
}

function upright_players()
{
	out = [];
	foreach ( p in playing_players() )
		if ( !( p laststand::player_is_in_laststand() ) )
			out[ out.size ] = p;
	return out;
}

function in_chamber( org )
{
	lo = tod_arena_data::chamber_min();
	hi = tod_arena_data::chamber_max();
	if ( !( org[ 0 ] > lo[ 0 ] && org[ 0 ] < hi[ 0 ] && org[ 1 ] > lo[ 1 ] && org[ 1 ] < hi[ 1 ]
		&& org[ 2 ] > lo[ 2 ] - TOD_ARENA_ENTER_Z && org[ 2 ] < hi[ 2 ] ) )
		return false;
	// docs/202 v2: the chamber is the haven's field, a circle inside that box
	r = tod_arena_data::chamber_r();
	if ( r <= 0 )
		return true;
	return Distance2DSquared( org, tod_arena_data::chamber_org() ) <= r * r;
}

// PURE: does this damage get cancelled as an arena fall?
function fall_guard_verdict( mod, org, active )
{
	return ( IS_TRUE( active ) && mod == "MOD_FALLING" && ( tod_arena_data::in_arena( org ) || tod_house_data::in_house( org ) ) );
}

// level.player_damage_callbacks: no fall damage while a fight runs (self = the player)
function arena_fall_guard( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, psOffsetTime )
{
	if ( !fall_guard_verdict( sMeansOfDeath, self.origin, level.tod_arena_active ) )
		return -1;
	if ( !IS_TRUE( self.tod_arena_fall_logged ) )
	{
		self.tod_arena_fall_logged = true;
		dev_log( "FALL_GUARD player=" + self GetEntityNumber() + " damage=" + iDamage + " at=" + self.origin + " (first this fight)" );
	}
	return 0;
}

// ---------------------------------------------------------------------------
// THE CHAMBER (floor 40)
// ---------------------------------------------------------------------------
function chamber_think()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	// the pad/beam FX are registered by _tod_teleport::init after the same
	// blackscreen (it sets level.tod_tp_trigs right after fx_register)
	for ( i = 0; i < 100 && !isdefined( level.tod_tp_trigs ); i++ )
		wait 0.1;
	if ( !isdefined( level.tod_tp_trigs ) )
		dev_log( "WARN teleport_fx_not_registered (the beam/charge FX may be missing)" );

	org = tod_arena_data::chamber_org();
	level.tod_arena_model = tod_teleport::spawn_der_teleporter( org, tod_arena_data::chamber_yaw() );
	// the arena's own teleporter on the dais: the landing point, the overcharge and
	// the ride home (dark while nobody is there, the pending chase while a fight
	// runs, ready for the return)
	level.tod_arena_pad = tod_teleport::spawn_der_teleporter( tod_arena_data::arena_dais(), 0 );
	t = Spawn( "trigger_radius_use", org + ( 0, 0, 32 ), 0, 110, 96 );
	if ( !isdefined( t ) )
	{
		dev_log( "INIT_FAILED reason=trigger_spawn org=" + org );
		return;
	}
	t TriggerIgnoreTeam();
	t SetCursorHint( "HINT_NOICON" );
	level.tod_arena_trig = t;
	level.tod_arena_state = "";
	level thread chamber_state_ticker( t, org );
	level thread chamber_notice_watch();
	dev_log( "INIT rev=2 chamber=" + org + " arena=" + tod_arena_data::arena_center() + " dais=" + tod_arena_data::arena_dais()
		+ " return=" + tod_arena_data::return_org() + " levels=" + TOD_ARENA_LEVELS + " sets=" + level.tod_arena_sets.size
		+ " spawns=" + tod_arena_data::arena_spawns().size + " gates=" + tod_arena_data::arena_gates().size
		+ " charge_s=" + TOD_ARENA_CHARGE_SECS + " purge=" + TOD_ARENA_PURGE );

	while ( true )
	{
		t waittill( "trigger", player );
		if ( !isdefined( player ) || !zm_utility::is_player_valid( player ) )
			continue;
		if ( player zm_utility::in_revive_trigger() )
			continue;
		why = chamber_refusal( player );
		if ( why != "" )
		{
			player PlaySound( "zmb_no_purchase" );
			if ( why == "not_all_inside" )
				player IPrintLnBold( "EVERYONE MUST BE INSIDE THE FIELD" );
			else if ( why == "haven_corrupted" )
				player IPrintLnBold( "DEFEAT THE GUARDIANS TO TAKE THIS HAVEN" );
			dev_log( "DENY player=" + player GetEntityNumber() + " reason=" + why + " level=" + level.tod_arena_level );
			wait 0.5;
			continue;
		}
		if ( TOD_ARENA_COST > 0 )
		{
			player zm_score::minus_to_player_score( TOD_ARENA_COST );
			player PlaySound( "zmb_cha_ching" );
		}
		dev_log( "START payer=" + player GetEntityNumber() + " cost=" + TOD_ARENA_COST + " level=" + level.tod_arena_level
			+ " players=" + playing_players().size );
		level.tod_arena_busy = true;
		chamber_refresh( t, org );
		arena_run( player );
		level.tod_arena_busy = false;
		chamber_refresh( t, org );
	}
}

// "" = go; otherwise the reason (logged; a sound always plays)
function chamber_refusal( player )
{
	if ( IS_TRUE( level.tod_arena_busy ) ) return "busy";
	if ( level.tod_arena_level > TOD_ARENA_LEVELS ) return "conquered";
	if ( !( level flag::get( "power_on" ) ) ) return "no_power";
	if ( isdefined( level.tod_haven_locked_fn ) && [[ level.tod_haven_locked_fn ]]( tod_arena_data::chamber_org() ) ) return "haven_corrupted";   // docs/202 v3
	if ( IS_TRUE( level.tod_upgrade_pause ) ) return "world_paused";
	if ( isdefined( level.tod_trial_box ) ) return "trial_running";
	foreach ( p in playing_players() )
		if ( !in_chamber( p.origin ) )
			return "not_all_inside";
	if ( TOD_ARENA_COST > 0 && !( player zm_score::can_player_purchase( TOD_ARENA_COST ) ) ) return "no_money";
	return "";
}

function chamber_state_ticker( t, org )
{
	level endon( "end_game" );
	while ( true )
	{
		chamber_refresh( t, org );
		wait 0.5;
	}
}

// THE NOTICE (v2.1): a player who has stood inside the chamber TOD_ARENA_NOTICE_MS is
// told the level they would be entering, once per level (the haven's own SAFE ZONE
// label has come and gone by then). A free lane (a centre print), no hint string.
function chamber_notice_watch()
{
	level endon( "end_game" );
	while ( true )
	{
		wait 0.5;
		foreach ( p in playing_players() )
		{
			if ( level.tod_arena_state != "ready" || !in_chamber( p.origin ) )
			{
				p.tod_arena_in_ms = 0;
				continue;
			}
			p.tod_arena_in_ms = ( isdefined( p.tod_arena_in_ms ) ? p.tod_arena_in_ms : 0 ) + 500;
			if ( p.tod_arena_in_ms < TOD_ARENA_NOTICE_MS )
				continue;
			if ( isdefined( p.tod_arena_notice ) && p.tod_arena_notice == level.tod_arena_level )
				continue;
			p.tod_arena_notice = level.tod_arena_level;
			notice = "BATTLE ARENA - LEVEL " + level.tod_arena_level + " OF " + TOD_ARENA_LEVELS;
			if ( level.tod_arena_level >= TOD_ARENA_LEVELS )
				notice = "BATTLE ARENA - THE FINAL FIGHT";   // docs/207
			p IPrintLnBold( notice );
			dev_log( "NOTICE player=" + p GetEntityNumber() + " level=" + level.tod_arena_level );
		}
	}
}

// hint + model on a STATE CHANGE only (four constant strings)
function chamber_refresh( t, org )
{
	state = "ready";
	if ( IS_TRUE( level.tod_arena_busy ) ) state = "busy";
	else if ( level.tod_arena_level > TOD_ARENA_LEVELS ) state = "done";
	else if ( !( level flag::get( "power_on" ) ) ) state = "power";
	else if ( isdefined( level.tod_haven_locked_fn ) && [[ level.tod_haven_locked_fn ]]( org ) ) state = "corrupted";   // docs/202 v3
	if ( state == level.tod_arena_state )
		return;
	level.tod_arena_state = state;
	switch ( state )
	{
		case "ready": t SetHintString( TOD_ARENA_HINT_READY ); break;
		case "power": t SetHintString( TOD_ARENA_HINT_POWER ); break;
		case "corrupted": t SetHintString( TOD_ARENA_HINT_GUARDIANS ); break;
		case "done":  t SetHintString( TOD_ARENA_HINT_DONE );  break;
		default:      t SetHintString( "" );                   break;
	}
	if ( isdefined( level.tod_arena_model ) )
		tod_teleport::model_state( level.tod_arena_model, ( state == "ready" ? "ready" : "off" ) );
	if ( state == "ready" && !isdefined( level.tod_arena_beam ) )
		level.tod_arena_beam = tod_teleport::spawn_beam( org );
	else if ( state != "ready" && isdefined( level.tod_arena_beam ) )
	{
		level.tod_arena_beam Delete();
		level.tod_arena_beam = undefined;
	}
	dev_log( "STATE " + state + " level=" + level.tod_arena_level );
}

// ---------------------------------------------------------------------------
// THE FIGHT
// ---------------------------------------------------------------------------
function arena_run( payer )
{
	level endon( "end_game" );
	lvl = level.tod_arena_level;
	set = pick_set();
	org = tod_arena_data::chamber_org();
	op = GetTime();

	// 1. THE CHARGE. Everything starts in THIS frame, threaded (fx_burst waits out
	// its whole lifetime: an inline call IS a delay), and the jump comes exactly
	// TOD_ARENA_CHARGE_SECS later. tools/test_battle_arena.js fails an inline
	// fx_burst anywhere in this file and checks this order against the v1 fixture.
	level thread tod_teleport::fx_burst( "tod_tp_charge", org + ( 0, 0, 40 ), TOD_ARENA_CHARGE_SECS + 0.5, "tod_tp_charge_field" );
	tod_perk_scatter::play_sound_at_origin( org, "tod_teleport_fire", 4 );
	banner = "BATTLE ARENA - LEVEL " + lvl;
	if ( lvl >= TOD_ARENA_LEVELS )
		banner = "BATTLE ARENA - THE FINAL FIGHT";   // docs/207
	foreach ( p in playing_players() )
		p IPrintLnBold( banner );
	dev_log( "CHARGE level=" + lvl + " set=" + set.name + " secs=" + TOD_ARENA_CHARGE_SECS );
	wait TOD_ARENA_CHARGE_SECS;

	// 2. hold the tower, open the arena (the jump's own frame)
	held = hold_tower();
	// THE DEALER'S HOUSE (docs/207): the last level is his, in his two rooms, in place of the waves
	if ( lvl >= TOD_ARENA_LEVELS )
	{
		// NO ARENA HIT MULTIPLIER IN THE HOUSE (2026-10-04, docs/210): he is its only attacker and carries his own
		// TOD_DEALER_MELEE_MULT 1.25 (_tod_bosses reads tod_keeper_dmg). With level 10's x2.35 on top, a swipe was
		// 45 x 2.35 x 1.25 = 131 - two hits down through Juggernog. Now 56: three at base health, five with Juggernog.
		level.tod_arena_dmg_mult = undefined;
		level.tod_arena_hp_round = hp_round( lvl );
		fight_reset();
		tod_teleport::discharge( org );
		if ( !tod_house::run( lvl, op ) )
		{
			dev_log( "ABORT reason=house_closed level=" + lvl );
			level.tod_arena_dmg_mult = undefined;
			level.tod_arena_hp_round = undefined;
			level.tod_arena_active = false;
			level notify( "tod_arena_fight_over" );
			release_tower( held );
			if ( TOD_ARENA_COST > 0 ) payer zm_score::add_to_player_score( TOD_ARENA_COST );   // refund: nothing happened
			return;
		}
		level notify( "tod_arena_fight_over" );
		arena_win( lvl, held );
		return;
	}
	zone = tod_arena_data::arena_zone();
	if ( !isdefined( level.zones[ zone ] ) )
	{
		dev_log( "ABORT reason=no_zone zone=" + zone );
		release_tower( held );
		if ( TOD_ARENA_COST > 0 ) payer zm_score::add_to_player_score( TOD_ARENA_COST );   // refund: nothing happened
		return;
	}
	zm_zonemgr::enable_zone( zone );
	// spawning ALLOWED while the party is inside: stock's zombie think still
	// walks level.zm_loc_types (built from active + allowed zones) before it
	// honours our chosen spot, and with the party here the arena is the only
	// active zone. Stock's own round spawner is held by the flag (hold_tower).
	level.zones[ zone ].is_spawning_allowed = true;
	level.tod_trial_box = arena_box();
	level.tod_arena_active = true;
	level.tod_arena_dmg_mult = dmg_mult( lvl );
	level.tod_arena_hp_round = hp_round( lvl );   // STATIC DIFFICULTY BY LEVEL (the knobs' block)
	fight_reset();
	tod_atmosphere::arena_music_start();   // 2026-09-28 (user): the boss music plays for the arena fight

	// 3. THE JUMP: the departure flash, the move, then (two frames on, so the
	// arrival host replicates after the riders do — the transit pads' v17.31
	// rule) the arrival flash on the dais.
	tod_teleport::discharge( org );
	land = tod_arena_data::arena_arrivals();
	dais = tod_arena_data::arena_dais();
	party = playing_players();
	for ( i = 0; i < party.size; i++ )
	{
		dst = land[ i % land.size ];
		face = VectorToAngles( dst - dais );   // outward: over the arena they will fight across
		party[ i ] SetOrigin( dst );
		party[ i ] SetPlayerAngles( ( 0, face[ 1 ], 0 ) );
		party[ i ].tod_arena_fall_logged = undefined;
	}
	level.tod_tp_stamp = ( isdefined( level.tod_tp_stamp ) ? level.tod_tp_stamp + 1 : 1 );
	dev_log( "JUMP level=" + lvl + " party=" + party.size + " ms_since_use=" + ( GetTime() - op ) + " (the charge is " + int( TOD_ARENA_CHARGE_SECS * 1000 ) + ")" );
	WAIT_SERVER_FRAME;
	WAIT_SERVER_FRAME;
	level thread tod_teleport::fx_burst( "tod_tp_kino", dais + ( 0, 0, 4 ), 3.0 );
	tod_teleport::discharge( dais );
	if ( isdefined( level.tod_arena_pad ) )
		tod_teleport::model_state( level.tod_arena_pad, "pending" );   // the yellow chase: the way home is shut until the win
	// v2.1: the readout (LEVEL N / GET READY) and the level's mood lights come up with the landing
	level thread hud_watch();
	hud_push( 0 );
	if ( TOD_ARENA_MOOD )
		level thread mood_start( lvl );
	dev_log( "ENTER level=" + lvl + " set=" + set.name + " party=" + party.size + " hp_mult=" + hp_mult( lvl ) + " dmg_mult=" + level.tod_arena_dmg_mult
		+ " zombies/wave=" + zombie_count( set, lvl ) + " refunded=" + held.refunded + " ms_since_use=" + ( GetTime() - op ) );
	wait TOD_ARENA_LAND_SECS;

	// 4. the waves (the camp tracker and the dais overcharge run alongside)
	level thread camp_watch();
	if ( TOD_ARENA_PURGE )
		level thread dais_purge( lvl );
	for ( w = 1; w <= TOD_ARENA_WAVES; w++ )
	{
		wave_begin( set, lvl, w );   // v2.1: the horn, the readout's wave line, the count's total
		spawn_wave( set, lvl, w );
		wait_wave_clear( lvl, w );
		if ( w < TOD_ARENA_WAVES )
			wait TOD_ARENA_WAVE_GAP;
	}
	level notify( "tod_arena_fight_over" );

	// 5. the win
	arena_win( lvl, held );
}

// per-fight state the director reads (cached once: the data functions build their arrays per call)
function fight_reset()
{
	level.tod_arena_spots = tod_arena_data::arena_spawns();
	level.tod_arena_kinds = tod_arena_data::arena_spawn_kinds();
	level.tod_arena_gates = tod_arena_data::arena_gates();
	level.tod_arena_last_spot = -1;
	level.tod_arena_gate_used = [];
	level.tod_arena_ai = [];
	foreach ( p in GetPlayers() )
	{
		p.tod_arena_camp_ms = 0;
		p.tod_arena_camp_org = undefined;
		p.tod_arena_camping = undefined;
	}
	// THE READOUT's state (v2.1): the wave's total, how many have risen, the elites
	// still to rise through their gates, the boss while he lives
	h = SpawnStruct();
	h.show = true;
	h.lvl = level.tod_arena_level;
	h.wave = 0;
	h.total = 0;
	h.risen = 0;
	h.pending = 0;
	h.boss = undefined;
	h.house = false;   // THE DEALER'S HOUSE (docs/207): the wave line reads THE FINAL FIGHT
	h.last_left = -1;
	h.last_wave = -1;
	h.last_boss = false;
	h.next = 0;
	level.tod_arena_hud = h;
}

// ---------------------------------------------------------------------------
// THE READOUT (v2.1): what TodArena.lua draws
// ---------------------------------------------------------------------------

// PURE (tools/test_battle_arena.js runs it): the enemies left in a wave = the ones
// not yet risen plus the ones still up; never fewer than the ones up (an open-ended
// add the total never counted cannot drive the count below the living).
function hud_left( total, risen, alive )
{
	left = total - risen + alive;
	if ( left < alive )
		left = alive;
	if ( left < 0 )
		left = 0;
	return left;
}

// one send to every playing player; `flags` = the one-shot bits (never the boss bit:
// that is read live here)
function hud_push( flags )
{
	h = level.tod_arena_hud;
	if ( !isdefined( h ) )
		return;
	left = hud_left( h.total, h.risen, arena_alive() );
	boss = ( isdefined( h.boss ) && IsAlive( h.boss ) );
	if ( boss )
	{
		// THE DEALER'S HOUSE (docs/207): the count line names him. (The else-branch's
		// TOD_ARENA_HUD_BOSS, THE KEEPER, retired with him 2026-10-05.)
		if ( IS_TRUE( h.boss.tod_dealer ) )
			flags = flags + TOD_ARENA_HUD_DEALER;
	}
	if ( IS_TRUE( h.house ) )
		flags = flags + TOD_ARENA_HUD_HOUSE;
	show = ( IS_TRUE( h.show ) ? 1 : 0 );
	// seven ints: the one LuiNotifyEvent shape past four values that stock itself uses
	// (test_tod_native_api.js: MP's show_outcome), and the level total is worth the slot
	foreach ( p in playing_players() )
		p LuiNotifyEvent( &"tod_arena", 7, show, h.lvl, TOD_ARENA_LEVELS, h.wave, TOD_ARENA_WAVES, left, flags );
	h.last_left = left;
	h.last_wave = h.wave;
	h.last_boss = boss;
	h.next = GetTime() + TOD_ARENA_HUD_RESEND_MS;
	if ( flags != 0 || show == 0 )
		dev_log( "HUD show=" + show + " level=" + h.lvl + " wave=" + h.wave + " left=" + left + " flags=" + flags );
}

// every 0.25 s while the fight runs: a changed count (a kill, a rise) or the re-send clock
function hud_watch()
{
	level endon( "end_game" );
	level endon( "tod_arena_fight_over" );
	while ( true )
	{
		wait 0.25;
		h = level.tod_arena_hud;
		if ( !isdefined( h ) )
			return;
		left = hud_left( h.total, h.risen, arena_alive() );
		boss = ( isdefined( h.boss ) && IsAlive( h.boss ) );
		if ( left != h.last_left || h.wave != h.last_wave || boss != h.last_boss || GetTime() >= h.next )
			hud_push( 0 );
	}
}

function hud_hide()
{
	h = level.tod_arena_hud;
	if ( !isdefined( h ) )
		return;
	h.show = false;
	hud_push( 0 );
}

// a wave begins: the horn to every player, the readout's wave line and total
function wave_begin( set, lvl, w )
{
	h = level.tod_arena_hud;
	nz = zombie_count( set, lvl );
	nm = elite_count( set, "mangler", lvl, w );
	nd = elite_count( set, "doppel", lvl, w );
	if ( set.elites == "both" )
		nd = nm;
	h.wave = w;
	h.total = nz + nm + nd;
	if ( lvl >= TOD_ARENA_LEVELS && w == TOD_ARENA_WAVES )
		h.total++;   // THE KEEPER
	h.risen = 0;
	h.pending = 0;
	foreach ( p in playing_players() )
		p PlaySoundToPlayer( TOD_ARENA_SND_WAVE, p );
	hud_push( TOD_ARENA_HUD_WAVE );
}

// ---------------------------------------------------------------------------
// THE GATE TELL (v2.1): an elite's gate charges and flashes before it rises
// ---------------------------------------------------------------------------
function gate_rise( kind, mult, lvl, w )
{
	org = elite_spot();
	level.tod_arena_hud.pending++;
	level thread gate_rise_think( kind, org, mult, lvl, w );
}

function gate_rise_think( kind, org, mult, lvl, w )
{
	level endon( "end_game" );
	level thread tod_teleport::fx_burst( "tod_tp_charge", org + ( 0, 0, 40 ), TOD_ARENA_GATE_TELL_SECS + 0.3, "tod_tp_charge_field" );
	tod_perk_scatter::play_sound_at_origin( org, TOD_ARENA_SND_GATE, 3 );
	dev_log( "GATE_TELL kind=" + kind + " level=" + lvl + " wave=" + w + " at=" + org + " secs=" + TOD_ARENA_GATE_TELL_SECS );
	wait TOD_ARENA_GATE_TELL_SECS;
	level thread tod_teleport::fx_burst( "tod_tp_flash", org + ( 0, 0, 4 ), 2.0 );
	spawn_elite( kind, org, mult, lvl, w );
	level.tod_arena_hud.pending--;
}

// ---------------------------------------------------------------------------
// THE MOOD LIGHTS (v2.1): the room's colour deepens with the level
// ---------------------------------------------------------------------------

// PURE: the level's glow index on the todPerkGlow lane (_tod_perk_lights.csc):
// 10 teal, 3 yellow, 4 orange, 1 red
function mood_index( lvl )
{
	if ( lvl >= 9 )
		return 1;
	if ( lvl >= 7 )
		return 4;
	if ( lvl >= 4 )
		return 3;
	return 10;
}

function mood_start( lvl )
{
	level endon( "end_game" );
	mood_end();   // never two sets
	orgs = tod_arena_data::arena_mood_orgs();
	hosts = [];
	foreach ( o in orgs )
	{
		h = Spawn( "script_model", o );
		if ( !isdefined( h ) )
			continue;
		h SetModel( "tag_origin" );
		hosts[ hosts.size ] = h;
	}
	level.tod_arena_mood = hosts;
	level.tod_arena_mood_idx = mood_index( lvl );
	wait 0.1;   // a snapshot: the client lane resolves tag_origin on the entity's dobj (the power wave's rule)
	foreach ( h in hosts )
		if ( isdefined( h ) )
			tod_perk_lights::set_glow( h, level.tod_arena_mood_idx );
	dev_log( "MOOD level=" + lvl + " index=" + level.tod_arena_mood_idx + " hosts=" + hosts.size + "/" + orgs.size );
}

// the dais host alone (the LAST of arena_mood_orgs): the overcharge's wind-up goes white
function mood_dais( idx )
{
	if ( !isdefined( level.tod_arena_mood ) || level.tod_arena_mood.size < 1 )
		return;
	h = level.tod_arena_mood[ level.tod_arena_mood.size - 1 ];
	if ( isdefined( h ) )
		tod_perk_lights::set_glow( h, idx );
}

function mood_end()
{
	if ( !isdefined( level.tod_arena_mood ) )
		return;
	hosts = level.tod_arena_mood;
	level.tod_arena_mood = undefined;
	foreach ( h in hosts )
		if ( isdefined( h ) )
			tod_perk_lights::set_glow( h, 0 );
	wait 0.5;
	foreach ( h in hosts )
		if ( isdefined( h ) )
			h Delete();
}

function arena_box()
{
	c = tod_arena_data::arena_center();
	h = tod_arena_data::arena_half();
	b = SpawnStruct();
	b.x1 = c[ 0 ] - h; b.x2 = c[ 0 ] + h;
	b.y1 = c[ 1 ] - h; b.y2 = c[ 1 ] + h;
	b.z1 = c[ 2 ] - 64; b.z2 = tod_arena_data::arena_top();   // v2: the whole height (the ring, the spokes, the dais)
	b.tod_arena = true;
	return b;
}

// ---------------------------------------------------------------------------
// THE DIRECTOR (docs/185 v2)
// ---------------------------------------------------------------------------

// PURE (tools/test_battle_arena.js runs it): the score of one spawn point.
// orgs = every player in the fight (the distance rules), eyes/fwds = the upright
// ones' eye points and view directions (who can see it), live = origins of the
// enemies already up, camper = a camping player's origin or undefined, repeat =
// true for the spot used last, jitter = a random 0..TOD_ARENA_SPAWN_JITTER.
// -1000000 = not allowed (somebody is closer than TOD_ARENA_SPAWN_MIN).
function spot_score( spot, kind, orgs, eyes, fwds, live, camper, repeat, jitter )
{
	dmin = 99999999;
	for ( i = 0; i < orgs.size; i++ )
	{
		dd = Distance( spot, orgs[ i ] );
		if ( dd < dmin )
			dmin = dd;
	}
	if ( dmin < TOD_ARENA_SPAWN_MIN )
		return -1000000;
	score = 0 - Abs( dmin - TOD_ARENA_SPAWN_IDEAL ) / TOD_ARENA_SPAWN_BAND;
	unseen = 0;
	for ( i = 0; i < eyes.size; i++ )
		if ( VectorDot( VectorNormalize( spot - eyes[ i ] ), fwds[ i ] ) < TOD_ARENA_SPAWN_SEEN_DOT )
			unseen++;
	if ( eyes.size > 0 )
		score = score + TOD_ARENA_SPAWN_UNSEEN * unseen / eyes.size;
	near = 0;
	for ( i = 0; i < live.size; i++ )
		if ( DistanceSquared( spot, live[ i ] ) < TOD_ARENA_SPREAD_R * TOD_ARENA_SPREAD_R )
			near++;
	score = score - TOD_ARENA_SPREAD_COST * near;
	if ( isdefined( camper ) )
	{
		dc = Distance( spot, camper );
		if ( dc < TOD_ARENA_CAMP_REACH )
			score = score + TOD_ARENA_CAMP_PULL * ( 1 - dc / TOD_ARENA_CAMP_REACH );
	}
	if ( repeat )
		score = score - TOD_ARENA_REPEAT_COST;
	return score + jitter;
}

// PURE: the index of the spawn point to use. Falls back to the point farthest
// from everyone when every point is too close (a party spread over the whole room).
function best_spot( spots, kinds, orgs, eyes, fwds, live, camper, last, jitters )
{
	best = -1;
	best_v = -999999;
	far = 0;
	far_d = -1;
	for ( i = 0; i < spots.size; i++ )
	{
		v = spot_score( spots[ i ], kinds[ i ], orgs, eyes, fwds, live, camper, i == last, jitters[ i ] );
		if ( v > best_v )
		{
			best_v = v;
			best = i;
		}
		dmin = 99999999;
		for ( j = 0; j < orgs.size; j++ )
		{
			dd = Distance( spots[ i ], orgs[ j ] );
			if ( dd < dmin )
				dmin = dd;
		}
		if ( dmin > far_d )
		{
			far_d = dmin;
			far = i;
		}
	}
	if ( best < 0 )
		return far;
	return best;
}

// PURE: the gate an elite comes through. A camper draws it to the legal gate
// nearest them; otherwise the legal gate farthest from the party, avoiding the
// last TOD_ARENA_GATE_MEMORY gates. Legal = at least TOD_ARENA_SPAWN_MIN from
// everyone; with none legal, the farthest gate.
function elite_gate( gates, orgs, camper, used )
{
	best = -1;
	best_v = -99999999;
	far = 0;
	far_d = -1;
	for ( i = 0; i < gates.size; i++ )
	{
		dmin = 99999999;
		for ( j = 0; j < orgs.size; j++ )
		{
			dd = Distance( gates[ i ], orgs[ j ] );
			if ( dd < dmin )
				dmin = dd;
		}
		if ( dmin > far_d )
		{
			far_d = dmin;
			far = i;
		}
		if ( dmin < TOD_ARENA_SPAWN_MIN )
			continue;
		v = dmin;
		if ( isdefined( camper ) )
			v = 100000 - Distance( gates[ i ], camper );
		for ( k = 0; k < used.size; k++ )
			if ( used[ k ] == i )
				v = v - 1000000;
		if ( v > best_v )
		{
			best_v = v;
			best = i;
		}
	}
	if ( best < 0 )
		return far;
	return best;
}

// PURE: a player's camping clock after one tick. Inside the circle (and on the
// same level) it runs on; anywhere else it starts again.
function camp_step( ms, moved, rise, step_ms )
{
	if ( moved > TOD_ARENA_CAMP_R || rise > 48 )
		return 0;
	return ms + step_ms;
}

// the party's view of the room, for the pure scorers
function party_view()
{
	v = SpawnStruct();
	v.orgs = [];
	v.eyes = [];
	v.fwds = [];
	foreach ( p in playing_players() )
	{
		v.orgs[ v.orgs.size ] = p.origin;
		if ( p laststand::player_is_in_laststand() )
			continue;
		v.eyes[ v.eyes.size ] = p GetEye();
		v.fwds[ v.fwds.size ] = AnglesToForward( p GetPlayerAngles() );
	}
	v.live = [];
	foreach ( ai in level.tod_arena_ai )
		if ( isdefined( ai ) && IsAlive( ai ) )
			v.live[ v.live.size ] = ai.origin;
	v.camper = arena_camper();
	v.camper_org = undefined;
	if ( isdefined( v.camper ) )
		v.camper_org = v.camper.origin;
	return v;
}

// -> the index into level.tod_arena_spots for the next ordinary zombie
function pick_zombie_spot()
{
	v = party_view();
	jit = [];
	for ( i = 0; i < level.tod_arena_spots.size; i++ )
		jit[ i ] = RandomFloat( TOD_ARENA_SPAWN_JITTER );
	i = best_spot( level.tod_arena_spots, level.tod_arena_kinds, v.orgs, v.eyes, v.fwds, v.live, v.camper_org, level.tod_arena_last_spot, jit );
	level.tod_arena_last_spot = i;
	level.tod_arena_pick_camper = isdefined( v.camper );
	return i;
}

// -> the origin of the gate the next elite comes through
function elite_spot()
{
	v = party_view();
	gates = level.tod_arena_gates;
	if ( !isdefined( gates ) || gates.size < 1 )
		gates = tod_arena_data::arena_gates();
	used = level.tod_arena_gate_used;
	if ( !isdefined( used ) )
		used = [];
	i = elite_gate( gates, v.orgs, v.camper_org, used );
	used[ used.size ] = i;
	if ( used.size > TOD_ARENA_GATE_MEMORY )
	{
		kept = [];
		for ( j = used.size - TOD_ARENA_GATE_MEMORY; j < used.size; j++ )
			kept[ kept.size ] = used[ j ];
		used = kept;
	}
	level.tod_arena_gate_used = used;
	dev_log( "GATE index=" + i + " at=" + gates[ i ] + " camper=" + ( isdefined( v.camper ) ? v.camper GetEntityNumber() : -1 ) );
	return gates[ i ];
}

// the longest-camping upright player past TOD_ARENA_CAMP_MS, or undefined
function arena_camper()
{
	best = undefined;
	best_ms = TOD_ARENA_CAMP_MS - 1;
	foreach ( p in upright_players() )
		if ( isdefined( p.tod_arena_camp_ms ) && p.tod_arena_camp_ms > best_ms )
		{
			best_ms = p.tod_arena_camp_ms;
			best = p;
		}
	return best;
}

// THE CAMP CLOCK: every 0.5 s while a fight runs. Logged on the edges.
function camp_watch()
{
	level endon( "end_game" );
	level endon( "tod_arena_fight_over" );
	while ( true )
	{
		wait 0.5;
		if ( IS_TRUE( level.tod_upgrade_pause ) )
			continue;
		foreach ( p in playing_players() )
		{
			if ( p laststand::player_is_in_laststand() || !isdefined( p.tod_arena_camp_org ) )
			{
				p.tod_arena_camp_org = p.origin;
				p.tod_arena_camp_ms = 0;
				continue;
			}
			was = IS_TRUE( p.tod_arena_camping );
			moved = Distance2D( p.origin, p.tod_arena_camp_org );
			rise = Abs( p.origin[ 2 ] - p.tod_arena_camp_org[ 2 ] );
			p.tod_arena_camp_ms = camp_step( p.tod_arena_camp_ms, moved, rise, 500 );
			if ( p.tod_arena_camp_ms == 0 )
				p.tod_arena_camp_org = p.origin;
			p.tod_arena_camping = ( p.tod_arena_camp_ms >= TOD_ARENA_CAMP_MS );
			if ( p.tod_arena_camping && !was )
				dev_log( "CAMP_START player=" + p GetEntityNumber() + " at=" + p.origin + " dais=" + tod_arena_data::on_dais( p.origin ) + " (spawns and the next elite pull toward them)" );
			else if ( !p.tod_arena_camping && was )
				dev_log( "CAMP_END player=" + p GetEntityNumber() + " at=" + p.origin );
		}
	}
}

// THE DAIS OVERCHARGE: the arena's own teleporter dumps its charge across the dais.
function dais_purge( lvl )
{
	level endon( "end_game" );
	level endon( "tod_arena_fight_over" );
	dais = tod_arena_data::arena_dais();
	wait TOD_ARENA_PURGE_FIRST;
	n = 0;
	while ( true )
	{
		while ( IS_TRUE( level.tod_upgrade_pause ) )
			wait 0.25;
		n++;
		level thread tod_teleport::fx_burst( "tod_tp_charge", dais + ( 0, 0, 40 ), TOD_ARENA_PURGE_WARN + 0.3, "tod_tp_charge_field" );
		tod_perk_scatter::play_sound_at_origin( dais, "tod_teleport_fire", 4 );
		mood_dais( TOD_ARENA_MOOD_WARN_IDX );   // v2.1: the dais light goes white for the wind-up (seen from the whole room)
		on = 0;
		foreach ( p in playing_players() )
		{
			if ( !tod_arena_data::on_dais( p.origin ) )
				continue;
			on++;
			if ( n == 1 || !IS_TRUE( p.tod_arena_purge_told ) )
			{
				p.tod_arena_purge_told = true;
				p IPrintLnBold( "THE DAIS IS OVERCHARGING - GET OFF IT" );
			}
		}
		dev_log( "PURGE_WARN n=" + n + " level=" + lvl + " players_on_dais=" + on );
		// v2.1: the wind-up warns whoever STEPS ON during it too (the first time each)
		for ( k = 0; k < int( TOD_ARENA_PURGE_WARN / 0.25 ); k++ )
		{
			wait 0.25;
			foreach ( p in playing_players() )
			{
				if ( !tod_arena_data::on_dais( p.origin ) || IS_TRUE( p.tod_arena_purge_told ) )
					continue;
				p.tod_arena_purge_told = true;
				p IPrintLnBold( "THE DAIS IS OVERCHARGING - GET OFF IT" );
				dev_log( "PURGE_WARN_LATE n=" + n + " player=" + p GetEntityNumber() );
			}
		}
		if ( isdefined( level.tod_arena_mood_idx ) )
			mood_dais( level.tod_arena_mood_idx );
		if ( IS_TRUE( level.tod_upgrade_pause ) )
		{
			dev_log( "PURGE_SKIP n=" + n + " reason=world_paused" );
			continue;
		}
		tod_teleport::discharge( dais );
		hit = 0;
		killed = 0;
		elites = 0;
		foreach ( p in playing_players() )
		{
			if ( !tod_arena_data::on_dais( p.origin ) || p laststand::player_is_in_laststand() )
				continue;
			dmg = int( p.maxhealth * TOD_ARENA_PURGE_PCT );
			if ( dmg < 1 )
				dmg = 1;
			p DoDamage( dmg, dais );
			hit++;
		}
		foreach ( ai in level.tod_arena_ai )
		{
			if ( !isdefined( ai ) || !IsAlive( ai ) || !tod_arena_data::on_dais( ai.origin ) )
				continue;
			if ( isdefined( ai.tod_boss_kind ) )
			{
				m = ai.maxhealth;
				if ( !isdefined( m ) || m < 1 )
					m = ai.health;
				ai DoDamage( int( m * TOD_ARENA_PURGE_ELITE_PCT ) + 1, dais );
				elites++;
			}
			else
			{
				ai DoDamage( ai.health + 666, dais );
				killed++;
			}
		}
		dev_log( "PURGE n=" + n + " level=" + lvl + " players_hit=" + hit + " zombies_killed=" + killed + " elites_hit=" + elites + " pct=" + TOD_ARENA_PURGE_PCT );
		wait TOD_ARENA_PURGE_EVERY - TOD_ARENA_PURGE_WARN;
	}
}

function spawn_wave( set, lvl, w )
{
	level endon( "end_game" );
	mult = hp_mult( lvl );
	nz = zombie_count( set, lvl );
	nm = elite_count( set, "mangler", lvl, w );
	nd = elite_count( set, "doppel", lvl, w );
	if ( set.elites == "both" ) nd = nm;
	dev_log( "WAVE_START level=" + lvl + " wave=" + w + " zombies=" + nz + " manglers=" + nm + " doppels=" + nd );

	// elites first, through the gates (the farthest, or the camper's nearest); v2.1:
	// each gate charges and flashes before its elite rises, the gates opening together
	for ( i = 0; i < nm; i++ )
		gate_rise( "mangler", mult, lvl, w );
	for ( i = 0; i < nd; i++ )
		gate_rise( "doppel", mult, lvl, w );

	spawner = level.zombie_spawners[ RandomInt( level.zombie_spawners.size ) ];
	made = 0;
	fails = 0;
	tally = [];
	pulled = 0;
	while ( made < nz )
	{
		while ( IS_TRUE( level.tod_upgrade_pause ) || zombie_utility::get_current_zombie_count() >= level.zombie_ai_limit || GetFreeActorCount() < 2 )
			wait 0.2;
		idx = pick_zombie_spot();
		pick = level.tod_arena_spots[ idx ];
		kind = level.tod_arena_kinds[ idx ];
		target = ArrayGetClosest( pick, playing_players() );
		sp = SpawnStruct();
		sp.origin = pick;
		sp.angles = ( 0, 0, 0 );
		if ( isdefined( target ) )
		{
			face = VectorToAngles( target.origin - pick );
			sp.angles = ( 0, face[ 1 ], 0 );
		}
		sp.script_noteworthy = "riser_location";   // the classic climb-out (zm_utility::move_zombie_spawn_location)
		sp.script_string = "find_flesh";
		sp.zone_name = tod_arena_data::arena_zone();
		guy = zombie_utility::spawn_zombie( spawner, spawner.targetname, sp );
		if ( isdefined( guy ) )
		{
			guy.tod_arena = true;
			guy.tod_zspeed_round_add = arena_speed_add();   // full sprint from level 1 (_tod_zombie_speed's per-zombie lane)
			guy thread arena_zombie_hp( mult );
			track( guy );
			level.tod_arena_hud.risen++;
			made++;
			if ( !isdefined( tally[ kind ] ) ) tally[ kind ] = 0;
			tally[ kind ]++;
			if ( IS_TRUE( level.tod_arena_pick_camper ) ) pulled++;
			if ( made <= 4 )
				dev_log( "SPAWN level=" + lvl + " wave=" + w + " n=" + made + " spot=" + idx + " kind=" + kind + " at=" + pick + " camper_pull=" + IS_TRUE( level.tod_arena_pick_camper ) );
		}
		else
		{
			fails++;
			if ( fails == 1 || fails % 20 == 0 )
				dev_log( "SPAWN_FAILED kind=zombie level=" + lvl + " wave=" + w + " made=" + made + "/" + nz + " fails=" + fails );
			if ( fails >= 60 )
				break;   // never hang the fight on a spawner that will not answer
		}
		wait TOD_ARENA_SPAWN_GAP;
	}
	// the gates still charging finish before the wave counts as spawned (bounded: a
	// gate that cannot rise its elite is logged by spawn_elite and given up)
	for ( i = 0; i < 80 && level.tod_arena_hud.pending > 0; i++ )
		wait 0.25;
	mix = "";
	foreach ( k, c in tally )
		mix = mix + " " + k + "=" + c;
	dev_log( "WAVE_SPAWNED level=" + lvl + " wave=" + w + " zombies=" + made + "/" + nz + " fails=" + fails + " by_kind:" + mix + " camper_pulled=" + pulled + " gates_pending=" + level.tod_arena_hud.pending );
}

// -> the round offset that puts an arena zombie at full sprint whatever the tower's round
function arena_speed_add()
{
	r = 1;
	if ( isdefined( level.round_number ) )
		r = level.round_number;
	add = TOD_ARENA_SPRINT_ROUND - r;
	if ( add < 0 )
		add = 0;
	return add;
}

// after stock's own health write AND _tod_zombie_speed's one-frame-deferred scale
function arena_zombie_hp( mult )
{
	self endon( "death" );
	wait 0.15;
	if ( !isdefined( self.health ) || self.health < 1 )
		return;
	h = int( self.health * mult + 0.5 );
	if ( h < 1 ) h = 1;
	self.health = h;
	self.maxhealth = h;
}

function spawn_elite( kind, org, mult, lvl, w )
{
	for ( tries = 0; tries < 40 && GetFreeActorCount() < 1; tries++ )
		wait 0.25;
	target = ArrayGetClosest( org, playing_players() );
	if ( !isdefined( target ) )
		return;
	face = VectorToAngles( target.origin - org );
	yaw = face[ 1 ];
	actor = undefined;
	if ( kind == "mangler" )
	{
		if ( GetFreeActorCount() >= 1 )
			actor = tod_mangler::spawn_at( org, target, ( 0, yaw, 0 ) );
		if ( isdefined( actor ) )
		{
			h = int( tod_doppelghast::hunter_hp( TOD_ARENA_ELITE_UNITS ) * mult + 0.5 );
			actor.health = h;
			actor.maxhealth = h;
		}
	}
	else
		actor = tod_doppelghast::spawn_hunter( org, target, int( TOD_ARENA_ELITE_UNITS * mult + 0.5 ) );
	if ( !isdefined( actor ) )
	{
		dev_log( "SPAWN_FAILED kind=" + kind + " level=" + lvl + " wave=" + w + " free_actors=" + GetFreeActorCount() );
		return;
	}
	actor.tod_arena = true;
	track( actor );
	level.tod_arena_hud.risen++;
	dev_log( "ELITE kind=" + kind + " level=" + lvl + " wave=" + w + " hp=" + actor.health + " ent=" + actor GetEntityNumber() + " at=" + org );
}

function track( ai )
{
	level.tod_arena_ai = array::remove_undefined( level.tod_arena_ai );
	level.tod_arena_ai[ level.tod_arena_ai.size ] = ai;
}

function arena_alive()
{
	n = 0;
	foreach ( ai in level.tod_arena_ai )
		if ( isdefined( ai ) && isalive( ai ) )
			n++;
	return n;
}

function wait_wave_clear( lvl, w )
{
	level endon( "end_game" );
	last_log = GetTime();
	last_n = arena_alive();
	last_drop = GetTime();
	while ( arena_alive() > 0 )
	{
		n = arena_alive();
		if ( n < last_n || IS_TRUE( level.tod_upgrade_pause ) )
			last_drop = GetTime();
		last_n = n;
		// A STUCK STRAGGLER must never trap the party in here: no kill for
		// TOD_ARENA_STALL_MS -> the ordinary zombies left are removed (elites
		// relocate themselves when stuck, _tod_bosses::pick_spawn_point inside
		// level.tod_trial_box, so they are left to the players).
		if ( GetTime() - last_drop > TOD_ARENA_STALL_MS )
		{
			k = 0;
			foreach ( ai in level.tod_arena_ai )
				if ( isdefined( ai ) && isalive( ai ) && !isdefined( ai.tod_boss_kind ) )
				{
					ai Kill();
					k++;
				}
			dev_log( "STRAGGLER_KILL level=" + lvl + " wave=" + w + " killed=" + k + " alive_before=" + n );
			last_drop = GetTime();
		}
		if ( GetTime() - last_log > 15000 )
		{
			dev_log( "WAVE_WAIT level=" + lvl + " wave=" + w + " alive=" + n + " party=" + playing_players().size );
			last_log = GetTime();
		}
		wait 0.25;
	}
	level.tod_arena_ai = [];
	dev_log( "WAVE_CLEAR level=" + lvl + " wave=" + w );
	if ( w < TOD_ARENA_WAVES )
	{
		// v2.1: the sting and WAVE CLEARED (the level's last wave gets the fanfare in arena_win)
		foreach ( p in playing_players() )
			p PlaySoundToPlayer( TOD_ARENA_SND_CLEAR, p );
		hud_push( TOD_ARENA_HUD_CLEARED );
	}
}

function arena_win( lvl, held )
{
	level endon( "end_game" );
	level.tod_arena_dmg_mult = undefined;
	level.tod_arena_hp_round = undefined;   // the tower round's health again (track_rounds, within 0.05 s)
	dev_log( "WIN level=" + lvl );

	// everyone gets a card: the downed are stood back up first
	foreach ( p in playing_players() )
		if ( p laststand::player_is_in_laststand() )
			p thread zm_laststand::auto_revive( p );
	// v2.1: the fanfare and LEVEL CLEARED on the readout. PK03 (2026-10-04): beating THE
	// DEALER (the house, the last level) is the run's victory and gets its own cue: "115"
	// fades under it, it rides his death line and lands on its major chord, and the channel
	// waits for it (the ride home's band plays when it has rung out; _tod_atmosphere). The
	// level fanfare stays for levels 1-9, and is the fallback while the teddy-bear song holds.
	victory = false;
	if ( lvl >= TOD_ARENA_LEVELS )
		victory = tod_atmosphere::house_victory_start();
	dev_log( "WIN_CUE level=" + lvl + " cue=" + ( victory ? "tod_house_victory" : TOD_ARENA_SND_LEVEL ) );
	if ( !victory )
	{
		foreach ( p in playing_players() )
			p PlaySoundToPlayer( TOD_ARENA_SND_LEVEL, p );
	}
	hud_push( TOD_ARENA_HUD_LEVEL );
	foreach ( p in playing_players() )
		p IPrintLnBold( "ARENA LEVEL " + lvl + " CLEARED" );
	if ( isdefined( level.tod_arena_pad ) )
		tod_teleport::model_state( level.tod_arena_pad, "ready" );   // the way home opens
	wait 1.0;

	// THE CARD, in a frozen world (set_world_pause first so nothing lands
	// between the win and the pick, then run_upgrade_event)
	tod_upgrades::set_world_pause( true );
	wait 1.5;
	tod_upgrades::run_upgrade_event();
	if ( IS_TRUE( level.tod_upgrade_pause ) && !isdefined( level.tod_station_pause_owner ) )
		tod_upgrades::set_world_pause( false );   // the empty-deal release (nobody had anything left)
	level.tod_arena_level = lvl + 1;
	dev_log( "DEALT level=" + lvl + " next=" + level.tod_arena_level );

	// back to the tower: the top bay. THE SAME BEAT AS THE WAY IN: the charge on
	// every rider and the dais in this frame (threaded), the ride TOD_ARENA_RETURN_SECS
	// later in the departure flash's own frame, the arrival flash two frames on.
	dst = tod_arena_data::return_org();
	rz = tod_arena_data::return_zone();
	if ( isdefined( level.zones[ rz ] ) && !IS_TRUE( level.zones[ rz ].is_enabled ) )
	{
		zm_zonemgr::enable_zone( rz );
		dev_log( "RETURN enabled_zone=" + rz );
	}
	dais = tod_arena_data::arena_dais();
	if ( isdefined( level.tod_arena_depart ) )
	{
		dais = level.tod_arena_depart;   // THE DEALER'S HOUSE (docs/207): the ride home charges on its dais
		level.tod_arena_depart = undefined;
	}
	op = GetTime();
	level thread tod_teleport::fx_burst( "tod_tp_charge", dais + ( 0, 0, 40 ), TOD_ARENA_RETURN_SECS + 0.5, "tod_tp_charge_field" );
	foreach ( p in playing_players() )
		tod_perk_scatter::play_sound_at_origin( p.origin, "tod_teleport_fire", 4 );
	wait TOD_ARENA_RETURN_SECS;
	tod_teleport::discharge( dais );
	party = playing_players();
	for ( i = 0; i < party.size; i++ )
	{
		ang = i * 360 / party.size;
		off = ( 0, 0, 0 );
		if ( party.size > 1 )
			off = ( Cos( ang ) * TOD_ARENA_RING, Sin( ang ) * TOD_ARENA_RING, 0 );
		party[ i ] SetOrigin( dst + off );
		party[ i ] SetPlayerAngles( ( 0, tod_arena_data::return_yaw(), 0 ) );
	}
	level.tod_tp_stamp = ( isdefined( level.tod_tp_stamp ) ? level.tod_tp_stamp + 1 : 1 );
	WAIT_SERVER_FRAME;
	WAIT_SERVER_FRAME;
	level thread tod_teleport::fx_burst( "tod_tp_kino", dst + ( 0, 0, 4 ), 3.0 );
	tod_teleport::discharge( dst );

	// the arena closes, the tower resumes
	if ( isdefined( level.tod_trial_box ) && IS_TRUE( level.tod_trial_box.tod_arena ) )
		level.tod_trial_box = undefined;
	level.tod_arena_active = false;
	if ( isdefined( level.tod_arena_pad ) )
		tod_teleport::model_state( level.tod_arena_pad, "off" );
	tod_atmosphere::arena_music_end();   // a random already-unlocked floor track comes back (2026-09-28)
	hud_hide();                   // v2.1: the readout fades with the ride home ...
	level thread mood_end();      // ... and the mood lights go out behind the party
	zone = tod_arena_data::arena_zone();
	if ( isdefined( level.zones[ zone ] ) )
		level.zones[ zone ].is_spawning_allowed = false;   // nobody there; never a stock spawn in an empty arena
	release_tower( held );
	level notify( "tod_stray_pump" );
	dev_log( "RETURN level=" + lvl + " party=" + party.size + " at=" + dst + " ride_ms=" + ( GetTime() - op ) + ( level.tod_arena_level > TOD_ARENA_LEVELS ? " CONQUERED" : "" ) );
	if ( level.tod_arena_level > TOD_ARENA_LEVELS )
		foreach ( p in playing_players() )
			p IPrintLnBold( "THE BATTLE ARENA IS CONQUERED" );
}

// ---------------------------------------------------------------------------
// THE TOWER WHILE NOBODY IS IN IT. Stock round spawning waits on the
// "spawn_zombies" flag (_tod_fall's flood_hold is the precedent); the leftover
// horde is deleted and refunded to the round (spawns are held, so the refund
// cannot push THE TWIST's clock mid-spawn — _tod_stray's warning), elites are
// deleted outright. Returns what it did so release_tower undoes exactly that.
// ---------------------------------------------------------------------------
function hold_tower()
{
	held = SpawnStruct();
	held.flag = false;
	held.refunded = 0;
	if ( level flag::exists( "spawn_zombies" ) && level flag::get( "spawn_zombies" ) )
	{
		level flag::clear( "spawn_zombies" );
		held.flag = true;
	}
	deleted = 0;
	ai = GetAITeamArray( level.zombie_team );
	foreach ( e in ai )
	{
		if ( !isdefined( e ) || !isalive( e ) || IS_TRUE( e.tod_arena ) || IS_TRUE( e.tod_is_partner ) )
			continue;
		// A HAVEN'S GUARDIANS STAY (2026-10-04, docs/210). The stairs pass inside every haven's wake band, so a party that
		// walks past a haven wakes its guardians; deleting them here sent their "death" and the haven counted them down -
		// a free cleanse (+500 each) for stepping into the arena. They stay inside their own field while the party is
		// away. tod_haven_guard is the haven's INDEX (0 is a real value), hence isdefined.
		if ( isdefined( e.tod_haven_guard ) )
			continue;
		if ( !isdefined( e.tod_boss_kind ) && !IS_TRUE( e.is_boss ) )
			held.refunded++;
		e Delete();
		deleted++;
	}
	if ( isdefined( level.zombie_total ) )
		level.zombie_total += held.refunded;
	dev_log( "HOLD spawn_flag_cleared=" + held.flag + " deleted=" + deleted + " refunded=" + held.refunded );
	return held;
}

function release_tower( held )
{
	if ( IS_TRUE( held.flag ) && level flag::exists( "spawn_zombies" ) )
		level flag::set( "spawn_zombies" );
	dev_log( "RELEASE spawn_flag_set=" + held.flag );
}
