// =============================================================================
// _tod_endless_rounds.gsc — THE TWIST: rounds never pause.
//
// Stock round flow (_zm.gsc round_think): spawn round -> [[round_wait_func]]
// waits until every zombie is DEAD -> round_over() waits
// func_get_delay_between_rounds() -> next loop iteration -> round_one_up()
// waits 2.5s of chalk fanfare -> spawning resumes.
//
// This map: the next round starts the moment the last zombie of the current
// round SPAWNS. Three stock override points, all verified against the stock
// mirror (tmp/bo3_stock_ref/scripts/zm/_zm.gsc):
//   level.round_wait_func            — DEFAULT'd only if undefined (:4130);
//                                      ours returns when zombie_total hits 0
//                                      (all SPAWNED), not when all are dead.
//   level.zombie_round_change_custom — replaces round_one_up (:4380) so there
//                                      is no 2.5s fanfare stall (round 1 keeps
//                                      the stock intro pacing).
//   level.func_get_delay_between_rounds — assigned unconditionally in zm::init
//                                      (:308); we re-assign AFTER
//                                      zm_usermap::main() so ours wins ->
//                                      round_over() waits 0.
//
// Self-regulating: round_spawning throttles on the zombie AI limit, so
// zombie_total only drains as zombies actually spawn. If players stop killing,
// spawning stalls at the cap and the round clock stalls with it.
//
// Call tod_endless_rounds::init() from the entry main() AFTER zm_usermap::main().
// =============================================================================

#using scripts\shared\array_shared;   // array::random (spawn-location fallback)
#using scripts\shared\flag_shared;
#using scripts\zm\_zm;
#using scripts\zm\_zm_audio;
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;   // beyond_gate + on_crown_island (the crown spawn filters)
#using scripts\zm\zm_tod2_cybercity\_tod_breather_data;   // v13.21 — lounge z-levels (the breather calm-down check)
#using scripts\zm\zm_tod2_cybercity\_tod_ambush;   // THE AMBUSH (docs/204) - where an ordinary zombie rises
#using scripts\zm\zm_tod2_cybercity\_tod_reach;   // THE PURSUIT (docs/200) — the reach filter that opens finale_spawn_selection

#insert scripts\shared\shared.gsh;

// ---- THE TRICKLE (docs/204, 2026-10-03, user: "This map should be more hectic than
// the first ... Lets check spawns and spawn rate speed") ---------------------------
// The per-zombie spawn delay = stock's curve x TOD_SPAWN_MULT, floored. It was a bare
// 0.83 / 0.25 in tod_spawn_delay (the 2026-08-29 tone-down, Workshop comments on the
// FIRST map), copied here unchanged - so this map trickled exactly as hard as map 1.
// 0.70 = +19% zombies a second at every round; the floor 0.20 = +25% at depth (the
// floor binds from about round 4 solo, round 1 in a full party). Both sit INSIDE the
// working band the ledger in tod_spawn_delay records (0.65-0.90).
// ROUND LENGTH IS HELD: under THE TWIST a round lasts (round size x delay), so a
// faster trickle alone would shorten every round and race the round counter (the
// health curve, the card deals, the elite unlocks all run on it). The round size
// rises with it (TOD_ROUND_MAX_AI / TOD_ROUND_AI_PER_PLAYER: stock 24 / 6 -> 28 / 7,
// +17%), so a round takes about as long as before and holds more zombies.
#define TOD_SPAWN_MULT           0.70
#define TOD_SPAWN_FLOOR          0.20
#define TOD_ROUND_MAX_AI         28     // stock zombie_max_ai 24
#define TOD_ROUND_AI_PER_PLAYER  7      // stock zombie_ai_per_player 6
// THE FALL (docs/160): the crown phase's trickle. Multiplies the resolved
// per-round delay while level.tod_fall_phase holds (written by _tod_fall:
// true from init, false at the seal), BEFORE the floor so the floor still
// binds. Round-granular like every other knob in this resolver — the seal's
// slowdown lands on the next rollover, which under THE TWIST is seconds. The
// sprint override in _tod_zombie_speed is the instant half of "overrun";
// this is the volume half. 1.0 = the crown trickles like everywhere else.
// 0.7 -> 1.0 (user 2026-10-04, first real playthrough: "Zombies are spawning in way
// too fast too early"; the crown IS the early game, rounds 1-8 of that run).
#define TOD_FALL_SPAWN_MULT      1.0
// THE RAMP (user 2026-10-04, same run: "Game should ramp up"). The early trickle is
// slower: round 1's delay x TOD_SPAWN_RAMP_EARLY, easing linearly to x1.0 on
// TOD_SPAWN_RAMP_FULL_ROUND, applied BEFORE the floor. Under THE TWIST a slower
// trickle also lengthens the early rounds, so the round counter (zombie health, the
// elite budget, the card deals) no longer races to round 6 in the first 80 s.
// RAMPAGE (the hard mode) eases out of it twice as fast. LOCKSTEP with the
// concurrency ramp (_tod_corpse_cleanup TOD_AI_RAMP_FULL_ROUND /
// TOD_RAMPAGE_AI_RAMP_FULL_ROUND); tools/test_spawn_ramp.js holds the pair.
#define TOD_SPAWN_RAMP_EARLY     1.6
#define TOD_SPAWN_RAMP_FULL_ROUND 30
#define TOD_RAMPAGE_SPAWN_RAMP_FULL_ROUND 15
// ---- RAMPAGE INDUCER (v14.20) --------------------------------------------
// The spawn-pacing half of hard mode. Applied in tod_spawn_delay() below; see
// the comment there for why this is round-granular rather than instant.
//
// 0.80 lands the effective multiplier at 0.83 x 0.80 = 0.664x stock, which is
// almost exactly the 0.65x the map ran as its MIDDLE setting before the two
// 2026-08-29 tone-downs — a pace this map has already shipped and been played
// at, rather than a new guess. That is the whole design of this feature: hand
// the pre-tone-down difficulty back to the players who wanted it, without
// taking it from the ones who did not.
#define TOD_RAMPAGE_SPAWN_MULT   0.80
// The floor has to come down with the multiplier or the squeeze is swallowed at
// depth (stock's own curve decays below 0.30 by round ~20, so a 0.25 floor
// would already be binding and 0.80 x anything would change nothing). 0.20 is
// the pre-tone-down floor. 0.20 -> 0.16 with THE TRICKLE (docs/204): the normal
// floor is 0.20 now, and the rampage floor stays a fifth under it.
#define TOD_RAMPAGE_SPAWN_FLOOR  0.16
// (THE LAST MILE's road-spawn knobs - TOD_FINALE_SPAWN_DELAY, TOD_FINALE_MIN_AHEAD_SQ and the CROWN-END WALL's
// three bands TOD_FINALE_BAND_* - retired whole 2026-10-05 (W2E) with the Map One ending they paced; their history
// and the user's 40/30/30 -> 25/25/50 ledger are in archive/map1_carryover/ and in git.)

#namespace tod_endless_rounds;

function init()
{
	level.round_wait_func = &tod_round_wait;
	level.zombie_round_change_custom = &tod_round_change;
	level.func_get_delay_between_rounds = &tod_between_round_delay;
	level.zombie_vars[ "zombie_between_round_time" ] = 0;   // belt + braces

	// FASTER SPAWN TRICKLE (user 2026-08-17 "rounds didn't seem to start up as
	// quickly"): with seamless rounds the real pacing clock is the per-zombie
	// spawn delay — stock starts at 2.0s (solo) and decays 0.95/round, so early
	// rounds trickle in and the round counter crawls. Chain the stock resolver
	// (KB pattern: save + delegate, never replace wholesale) and HALVE it,
	// floored at 0.15s. Also pre-set round 1's value directly — the resolver is
	// only consulted from round 2 on, and calling the stock func at init time
	// would crash (it switches on level.players.size, which is 0 here).
	level.tod_stock_spawn_delay_func = level.func_get_zombie_spawn_delay;
	level.func_get_zombie_spawn_delay = &tod_spawn_delay;
	level.zombie_vars[ "zombie_spawn_delay" ] = 2.0 * TOD_SPAWN_MULT * TOD_SPAWN_RAMP_EARLY * TOD_FALL_SPAWN_MULT;   // round 1 = the resolver's own answer for round 1 in the crown (THE RAMP, 2026-10-04). Stock solo round 1 = 2.0, at TOD_SPAWN_MULT (docs/204; was 1.66 = 0.83x). PING-PONG LEDGER: 0.5x too hot (08-20) -> 0.8x "too slow" (08-22) -> 0.65x -> 0.75x (08-29 first tone-down) -> 0.83x (08-29 SECOND tone-down, Workshop difficulty comments — DELIBERATELY past the old 0.8 bound: that bound predates sprinters, scaled co-op elites and the faster speed curve, and live player feedback outranks it. New working band 0.65-0.90.)

	// v13.24 (same order): TRASH ZOMBIE HP -10% AT EVERY ROUND. Scaling the
	// stock start (150->135) and per-round increase (100->90) by 0.9 with the
	// compounding multiplier untouched is EXACTLY -10% at every round number
	// (pre-10 linear and post-10 exponential alike). Bosses keep their own
	// curves (deliberate); sprinters read level.zombie_health x20 at
	// conversion so they inherit the -10% automatically, as do all
	// %-of-health effects. The vendored packs that read zombie_health_start
	// (mechz, fury) use it as a RATIO base, which a uniform scale preserves.
	// POWER SCALE (2026-09-25): map 1's 135 / 90 at one tenth. Stock's integer
	// loop drifts a few % low at these small numbers, so _tod_power_scale holds
	// level.zombie_health on map 1's EXACT curve / 10 and _tod_zombie_speed writes
	// it onto every fresh spawn; these only keep stock's own recompute close.
	level.zombie_vars[ "zombie_health_start" ]    = 13.5;
	level.zombie_vars[ "zombie_health_increase" ] = 9;

	// One-time pre-round-1 stall (stock waits 2s before the first spawn pass).
	level.zombie_round_start_delay = 1;

	// THE TRICKLE's other half (docs/204): more zombies per round so the faster
	// trickle does not shorten the round. Stock reads both fresh in
	// get_zombie_count_for_round every round; its early-round table (x0.25 on
	// round 1 ... x0.9 on round 5) still applies on top.
	level.zombie_vars[ "zombie_max_ai" ] = TOD_ROUND_MAX_AI;
	level.zombie_vars[ "zombie_ai_per_player" ] = TOD_ROUND_AI_PER_PLAYER;

	// THE AMBUSH (docs/204): a share of the ordinary spawns climb out round a player.
	tod_ambush::init();

	// THE SPAWN SELECTOR (the name is the Map One ending's, kept: the gates and the
	// peers know it by it). This is stock's own supported override
	// (_zm_spawner.gsc:2950, shipped precedent zm_giant.gsc:1014), so we are not
	// patching the spawn path — just choosing from the candidate list stock
	// already built: the reach filter, the crown filters, THE AMBUSH, else stock's
	// random corner.
	level.zm_custom_spawn_location_selection = &finale_spawn_selection;
}

// v13.21 — TRUE while any player stands in a rest stop (the "extra tone down in
// breather rooms"). SINCE docs/202 v3 (user 2026-10-03, tweak #2) THE REST IS THE
// SAFE FIELD, not the hall round it: level.tod_haven_calm_fn (_tod_haven::calm_any)
// is true only while a living player stands INSIDE a haven's force field that has
// been taken from its guardians - the loggia, where kills pay in full, no longer
// calms the spawn clock, and a corrupted haven never does. Checked per spawn-delay
// resolve, so a player stepping out re-arms full pace within one spawn. Co-op
// note, deliberate: one resting player calms the whole spawn clock — the
// alternative (per-zone rate) does not exist in stock's single global delay, and
// a team regrouping in a sanctuary is exactly when the map should breathe.
function tod_player_in_breather()
{
	if ( isdefined( level.tod_haven_calm_fn ) )
		return [[ level.tod_haven_calm_fn ]]();
	return false;
}

// -> the spawn location stock should use, from the candidates it offers.
//
// THIS MUST BEHAVE LIKE STOCK. The hook is GLOBAL — it is consulted on every
// zombie of every round — so its fallback returns array::random(spots), which is
// verbatim what stock does when no override is set. Getting that wrong would
// silently re-pace the whole map. (Its finale-only branches - the lane lottery,
// the sealed hall and THE LAST MILE's road picker - retired whole with the Map
// One ending, 2026-10-05.)
// ONE DELIBERATE EXCEPTION (THE PURSUIT, docs/200, 2026-10-02): the reach filter
// below drops the risers from which no player can be walked to. It does not
// re-pace anything — the pick is still array::random over the survivors — it only
// stops stock raising zombies on a catch deck under a player on the ledge above
// (the zone graph is two-way, so that floor is an "active" zone).
function finale_spawn_selection( spots )
{
	if ( !isdefined( spots ) || spots.size == 0 )
		return undefined;

	// FIRST, before every other filter: they all keep the same fail-safe shape
	// (an empty result leaves the pool alone), and so does this one.
	spots = tod_reach::filter_spawns( spots );

	// WHILE THE GATE IS SHUT, the causeway and the citadel behind it are
	// pathing-severed from the terrace (_tod_finale::gate_init DisconnectPaths).
	// roof_zone spans all three, though, so the moment a player buys the roof
	// door those risers join the pool — and anything that rose on them would be
	// stranded on a bridge with no route to a player, holding a slot under the
	// actor cap until the map ended. Drop them until gate_open() says otherwise.
	if ( !IS_TRUE( level.tod_gate_open ) )
	{
		inside = [];
		for ( i = 0; i < spots.size; i++ )
		{
			sp = spots[ i ];
			if ( !isdefined( sp ) || !isdefined( sp.origin ) )
				continue;
			if ( tod_crown_data::beyond_gate( sp.origin ) )
				continue;
			inside[ inside.size ] = sp;
		}
		// If EVERY candidate is past the gate something upstream is wrong; take
		// stock behaviour over refusing to spawn at all.
		if ( inside.size > 0 )
			spots = inside;
	}
	// docs/163 THE CUT: once THE FALL has sealed, the crown island (the hall
	// and its jump-pad stub) is unreachable until the bottom return opens it — the
	// gate is shut and the pad only goes one way — so anything rising there
	// strands an actor. _tod_fall turns crown_zone's spawning off at the seal;
	// this is the backstop for stock's manage_zones failsafe, which switches
	// the START zone (crown_zone) back on whenever no occupied zone allows
	// spawning. Same fail-safe shape as every filter in this function: a pool
	// that is ALL island is left to stock (stock cannot take "no spot").
	if ( IS_TRUE( level.tod_fall_sealed ) && !IS_TRUE( level.tod_fall_return_open ) && tod_crown_data::jumppad_enabled() )
	{
		off_island = [];
		for ( i = 0; i < spots.size; i++ )
		{
			sp = spots[ i ];
			if ( !isdefined( sp ) || !isdefined( sp.origin ) )
				continue;
			if ( tod_crown_data::on_crown_island( sp.origin ) )
				continue;
			off_island[ off_island.size ] = sp;
		}
		if ( off_island.size > 0 )
			spots = off_island;
	}
	// THE AMBUSH (docs/204, 2026-10-03): a share of the ordinary spawns climb out of
	// the navmesh round an upright player (ahead, behind out of sight, or on a
	// flank) instead of on an authored corner. It re-applies every rule above to its
	// own point (reach, gate, island, havens, arena) and answers undefined - the
	// corners - when it has nothing. self is the zombie being spawned (stock calls
	// this from its spawn thread).
	ambush = self tod_ambush::pick( spots );
	if ( isdefined( ambush ) )
		return ambush;
	return array::random( spots );
}

// THE RAMP's trickle factor (2026-10-04, see TOD_SPAWN_RAMP_EARLY): EARLY on round 1,
// easing linearly to 1.0 on the full round (rampage: TOD_RAMPAGE_SPAWN_RAMP_FULL_ROUND).
// Wait-free and pure (tools/test_spawn_ramp.js evaluates it).
function spawn_ramp_mult( n_round )
{
	full = TOD_SPAWN_RAMP_FULL_ROUND;
	if ( IS_TRUE( level.tod_rampage_on ) )
		full = TOD_RAMPAGE_SPAWN_RAMP_FULL_ROUND;
	if ( !isdefined( n_round ) || n_round <= 1 )
		return TOD_SPAWN_RAMP_EARLY;
	if ( n_round >= full )
		return 1.0;
	t = ( n_round - 1 ) / ( full - 1 );
	return TOD_SPAWN_RAMP_EARLY + ( 1.0 - TOD_SPAWN_RAMP_EARLY ) * t;
}

// Per-round spawn delay: stock curve at 0.8x, floor 0.3s (was 0.5x/0.15 —
// "rounds are actually too aggressive", user 2026-08-20; the seamless-round
// twist stays, the trickle just breathes more).
function tod_spawn_delay( n_round )
{
	// v13.24 (user 2026-08-29, SECOND tone-down, driven by Workshop
	// difficulty comments: "another 10% less aggressive" + "breather zone
	// gets an extra 5%"): 0.75x/0.23 -> 0.83x/0.25, breather x1.13 -> x1.19
	// (lounges now run at ~0.99x ≈ STOCK pace — a true rest). FULL PING-PONG
	// LEDGER: 0.5x/0.15 too hot (08-20), 0.8x/0.3 "too slow" (08-22),
	// 0.65x/0.2 middle, 0.75x/0.23 first tone-down (08-29). 0.83 sits PAST
	// the old 0.8 bound DELIBERATELY — that bound predates sprinters, scaled
	// co-op elites and the round-18 speed ramp, and live player feedback
	// outranks a stale measurement. New working band 0.65-0.90. Player-count
	// scaling rides the STOCK resolver underneath, so these percentages hold
	// at every lobby size.
	d = [[ level.tod_stock_spawn_delay_func ]]( n_round );
	d = d * TOD_SPAWN_MULT;   // docs/204: 0.83 -> 0.70 (THE TRICKLE, see the define)
	d = d * spawn_ramp_mult( n_round );   // THE RAMP (2026-10-04): slower early, x1.0 from round 30 (rampage: 15)
	if ( IS_TRUE( level.tod_fall_phase ) )
		d = d * TOD_FALL_SPAWN_MULT;   // docs/160: the crown phase (see the define)
	// RAMPAGE INDUCER (v14.20, user 2026-08-30: "I also want spawn
	// aggressiveness to be buffed with rampage inducer. Not sure if we can make
	// that dynamic").
	//
	// YES, IT IS DYNAMIC — but at ROUND granularity, not instantly. This
	// resolver is consulted ONCE PER ROUND by stock (_zm.gsc:4502) and its
	// result is stamped into zombie_vars["zombie_spawn_delay"] for the whole
	// round, so a toggle lands on the NEXT round rollover. Under THE TWIST that
	// is seconds away, which is why this is a resolver change and not a direct
	// zombie_vars write (a direct write is only worth it for a change that
	// cannot wait for a rollover; live-test lesson 2026-08-29).
	//
	// A MULTIPLIER, applied BEFORE the floor so the floor still binds. The
	// floor tightens too (0.25 -> TOD_RAMPAGE_SPAWN_FLOOR 0.20) or the
	// multiplier would be swallowed whole at depth, where stock's own curve has
	// already decayed past it.
	fl = TOD_SPAWN_FLOOR;   // docs/204: 0.25 -> 0.20
	if ( IS_TRUE( level.tod_rampage_on ) )
	{
		d = d * TOD_RAMPAGE_SPAWN_MULT;
		fl = TOD_RAMPAGE_SPAWN_FLOOR;
	}
	if ( d < fl )
		d = fl;
	// The breather relief is applied AFTER the rampage squeeze on purpose: the
	// lounges stay a real rest even in hard mode, just a less generous one
	// (0.83 x 0.80 x 1.19 ~= 0.79x stock, against 0.99x normally).
	if ( tod_player_in_breather() )
		d = d * 1.19;

	ramp_log( "DELAY round=" + n_round + " delay=" + d + " ramp=" + spawn_ramp_mult( n_round ) + " fall=" + IS_TRUE( level.tod_fall_phase ) + " rampage=" + IS_TRUE( level.tod_rampage_on ) + " breather=" + tod_player_in_breather() );
	return d;
}

// [TOD_RAMP] console-only (dev or diag): one line per round with the resolved trickle.
function ramp_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_RAMP] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// Replaces stock round_wait (waits for all DEAD). Ours: wait until the round's
// spawn budget is fully spent — every zombie has spawned — then hand the round
// loop straight on. Carry-over zombies from the previous round stay alive and
// blend into the next wave: "the round never ended."
function tod_round_wait()
{
	level endon( "restart_round" );

	wait 0.5;   // let the round_spawning thread establish totals (trimmed from stock's 1s)

	// Wait for round_spawning to set this round's zombie_total (bounded so a
	// hiccup can never wedge the round loop forever).
	waited = 0;
	while ( ( !isdefined( level.zombie_total ) || level.zombie_total <= 0 ) && waited < 10 )
	{
		wait 0.1;
		waited += 0.1;
	}

	// THE TWIST: return once every zombie of this round has SPAWNED.
	while ( isdefined( level.zombie_total ) && level.zombie_total > 0 && !( level flag::get( "end_round_wait" ) ) )
	{
		wait 0.1;
	}

	// NO ROUND-OVER JINGLE (map 1's v19.55, ported 2026-10-04, docs/208; its lead tester:
	// "Audio overlap is still at start of game where you hear zombies music overlap with the
	// music you have played"). A call to stock's music-state player for the "round_end"
	// state lived here and played the "roundend1" music cue every time a round's last
	// zombie SPAWNED, on top of _tod_atmosphere's own track, which owns the music channel.
	// The early rounds are short, so it stacked right at the start. There is no round end
	// to announce on this map: the round never ends.
}

// Replaces the round_one_up fanfare block. Round 1 keeps the stock intro
// (level-start vox + HUD timing); after that, no stall — the round number HUD
// still updates (SetRoundsPlayed drives it, not this hook).
function tod_round_change()
{
	if ( level.first_round )
	{
		zm::round_one_up();
		return;
	}
}

// round_over() waits this between rounds. Zero = seamless.
function tod_between_round_delay()
{
	return 0;
}
