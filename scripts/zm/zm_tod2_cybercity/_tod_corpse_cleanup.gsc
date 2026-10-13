// =============================================================================
// _tod_corpse_cleanup.gsc — delete zombie bodies so they never eat the actor cap
//
// WHY THIS EXISTS (user 2026-08-25: "can we go to 45 for the whole game not just
// boss. I think we need to be carefull and make sure bodies get clean up
// quickly. Maybe couple seconds after dying.")
//
// THE CAP IS TWO NUMBERS, NOT ONE, and they count different things:
//   level.zombie_ai_limit     stock 24 -> ai_limit_for_party() 30/35/40/45
//       gates get_current_zombie_count() = GetAITeamArray(zombie_team) MINUS
//       anything carrying ignore_enemy_count. Every boss in this map sets that,
//       so this number is LIVE ZOMBIES ONLY — bosses are invisible to it.
//   level.zombie_actor_limit  stock 31 -> TOD_ACTOR_LIMIT 60
//       gates get_current_actor_count() = GetAiSpeciesArray(zombie_team,"all")
//       PLUS GetCorpseArray() (zombie_utility.gsc:2264-2276). That one counts
//       EVERYTHING: zombies, bosses, and every body still lying on the floor.
// Neither is an engine limit — both are `if (!isdefined(...))` defaults in
// _zm.gsc:337-343. The real ceiling is 64, netcode-imposed.
//
// SO THE BODIES ARE THE PROBLEM. Raise the live cap to 45 without touching
// corpses and the actor count is 45 zombies + up to a dozen elites + every body
// killed in the last few seconds — straight through 60 and into stock's spawn
// stall. A merely Ghost()'d corpse is invisible but STILL COUNTS. Only Delete()
// takes it out of the array.
//
// THIS IS NOT A MEMORY LEAK, AND THE DISTINCTION MATTERS (user: "This is where
// possible memory leak can break the game"). A corpse is a normal server entity
// on stock's own timer — the engine recycles it, and stock's spawn gate calls
// clear_all_corpses() the moment the actor count is hit (_zm.gsc:3740-3744), so
// bodies can never accumulate without bound even with this file deleted. What
// they CAN do is sit in the count long enough to throttle spawning, which reads
// in game as the horde going thin. Deleting them early strictly REDUCES entity
// pressure; it never adds any.
// The one genuine unbounded-growth risk in this design would be the per-corpse
// thread itself, so it is a straight line with one wait and no loop, it holds no
// reference after Delete(), and it cannot outlive the entity (see below).
//
// PORTED from map 1's _acc_corpse_cleanup.gsc, which ships this to run
// ACC_AI_LIMIT 50 / ACC_ACTOR_LIMIT 56. Two deliberate changes:
//   * LINGER 2s, not 0. Map 1 vanishes bodies on the death frame. The ask here
//     was "a couple seconds after dying", so the body drops, reads as a kill,
//     and then goes.
//   * THE LINGER IS ADAPTIVE. Two seconds of visible body is a luxury, and it is
//     the first thing given up when the board is full — see corpse_remove().
//     Map 1 did not need this because its linger was zero.
// =============================================================================

#using scripts\shared\callbacks_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\util_shared;

#using scripts\shared\ai\zombie_utility;
#using scripts\zm\_zm_spawner;
#using scripts\zm\_zm_utility;    // play_sound_at_pos

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#namespace tod_corpse_cleanup;

// LIVE ZOMBIES. 45 (user 2026-08-25), against stock 24 and map 1's proven 50.
// Under map 1's own note — "4-player netcode may strain near the ceiling; if it
// rubber-bands, drop toward ~40" — 45 sits between its shipped 50 and that
// floor, which is the cautious read of a number that is already known to work
// one map over.
// PARTY-AWARE SINCE v18.11 (user 2026-09-07: "People are seriously complaining
// about the difficulty. Is there a limit of zombies on map by players?").
//
// THE ANSWER WAS NO, AND THAT WAS THE PROBLEM. This was a flat 45 for one player
// or four. Stock's default is 24 solo, so a solo player was holding ~1.9x stock
// concurrency and FOUR TIMES the per-player pressure of a quad (45 each against
// 11.25 each) - on an open staircase 160 units wide with a drop on one side.
//
// AND ELITES DO NOT COUNT TOWARD IT. Every elite in this map sets
// ignore_enemy_count, so this number is trash zombies ONLY: the Panzer, the
// Protectors, the Reavers, the hounds and the sprinters all stand on TOP of it.
//
// THE LADDER: 30 / 35 / 40 / 45. The quad number is unchanged, deliberately -
// 45 is the figure the user asked for by name on 2026-08-25 and the one co-op
// has actually been played on, so this cut cannot touch a party size that has
// evidence behind it. Solo still sits well above stock's 24, so the map keeps
// its identity; it just stops asking one player to hold a four-player wall.
//
// ⚠️ THIS IS THE THIRD SOLO NERF IN THREE VERSIONS - v18.1 cut the combined
// elite roof 12 -> 5 and removed the solo horde-health surcharge, and neither
// has been played. If solo now reads TOO EASY, this ladder is the first thing to
// walk back, not the elite roof: concurrency is the lever a player feels most
// directly, and it is the one that moved last.
//
// A NOTE ON v18.1's OWN AUDIT: its table recorded this row as "24 solo / 9.3
// trio", figures computed from coop_ai_limit() - which had been DEAD since
// v10.26. The one number that most defines solo pressure was mis-recorded in the
// pass written to relieve solo. Read ai_limit_for_party(), never a quoted total.
// ⭐ 2026-09-28 (user: "since players get such better and stronger classes I do want it to be a bit
// more hectic ... increase the max enemies on map to the max ... make sure we dont crash ... 4 player
// coop will be max. We can lower it for less people but i want it more chaotic then the tower of doom 1
// map"): 36 / 42 / 48 / 54, +20% over Tower of Doom 1's 30 / 35 / 40 / 45 at every party size.
// WHY 54 IS THE MAX AND NOT MORE: the engine's actor pool is 64 (netcode). Everything shares it -
// live zombies, elites (they ignore this cap but not the pool), bodies still in their linger, and the
// Necromancer's summoned allies. TOD_ACTOR_LIMIT (60) holds 4 free for elites / summons (each spawner
// asks for 2-4 free before it spawns), and a quad late round stands at ~54 zombies + ~6 elites = 60.
// Anything over that only waits in stock's own gate (clear_all_corpses + 0.1 s), it never crashes -
// and ai_limit_watch now also subtracts every live ALLIED actor from the zombie gate, so a full board
// plus a Necromancer's hounds and Mangler can never run the engine pool dry.
#define TOD_AI_LIMIT_SOLO   36
#define TOD_AI_LIMIT_PER    6     // per extra player
#define TOD_AI_LIMIT_MAX    54    // the quad figure (Tower of Doom 1: 45)
#define TOD_AI_LIMIT_CEIL   58    // the absolute top, rampage included (quad 54 + 10 would stand past the actor gate)
// RAMPAGE (v18.74, user 2026-09-10: "zombies alive at once jumps 10"). ADDED
// on top of the party figure AFTER the clamp, so hard mode is 40/45/50/55 —
// it was a flat 45 from v18.11, which at quad was no step at all. 55 + the
// rampage elite roof (14 at quad) is over TOD_ACTOR_LIMIT 60; that is the
// documented-safe overflow (stock clears corpses and waits 0.1 s), so at quad
// the last few of the 55 arrive as bodies leave rather than all standing.
#define TOD_RAMPAGE_AI_LIMIT_ADD 10
// THE RAMP (user 2026-10-04, the first real playthrough: "Zombies are spawning in way
// too fast too early ... Game should ramp up. Even the max amount is the max max. Maybe
// early rounds should have a max - x until maybe round 30 where it actually allows the
// cap"). ai_limit_for_party() is the LATE-GAME figure; ai_limit_now() is what stands at
// once THIS round: TOD_AI_RAMP_START_FRAC of it on round 1, rising linearly to all of
// it on TOD_AI_RAMP_FULL_ROUND. RAMPAGE (the hard mode) climbs it twice as fast
// (TOD_RAMPAGE_AI_RAMP_FULL_ROUND) on top of its +10. The Battle Arena reads its own
// fixed difficulty round (level.tod_arena_hp_round) while a fight runs.
// LOCKSTEP: the spawn trickle ramps on the same two rounds (_tod_endless_rounds
// TOD_SPAWN_RAMP_FULL_ROUND / TOD_RAMPAGE_SPAWN_RAMP_FULL_ROUND; tools/test_spawn_ramp.js).
#define TOD_AI_RAMP_START_FRAC   0.34
#define TOD_AI_RAMP_FULL_ROUND   30
#define TOD_RAMPAGE_AI_RAMP_FULL_ROUND 15
#define TOD_AI_RAMP_MIN          10   // never fewer than this at once (a 0-player frame, a partner reserve)

// LIVE ZOMBIES + BOSSES + BODIES. The headroom over TOD_AI_LIMIT is 15, and it
// is sized for the worst realistic board rather than the average one:
//     45 live zombies (the QUAD ceiling - ai_limit_for_party() since v18.11;
//        smaller parties leave more headroom, never less, so this sizing holds)
//   +  up to ~12 elites (panzer 1 + protectors 8 + reavers 3; the hound
//      director's own combined guard is 9)
//   +  bodies killed inside the linger window
// which can exceed 60 in a quad late round — and that is FINE, because going
// over does not crash: stock's gate calls clear_all_corpses() and waits 0.1s
// (_zm.gsc:3740). The adaptive linger below is what keeps it from getting there
// in the first place. 60 also leaves 4 under the 64 engine ceiling.
#define TOD_ACTOR_LIMIT     60

// How long a body stays visible before it is deleted, when there is room for it.
#define TOD_CORPSE_LINGER   2.0

// THE SAFETY VALVE. When the actor count is within this many of TOD_ACTOR_LIMIT,
// the linger is skipped and the body is deleted on the spot. This is what makes
// the 2s cosmetic rather than structural: at a quiet moment you get bodies on
// the floor, and the instant the board fills they stop existing, so corpses can
// never be the reason a zombie fails to spawn.
#define TOD_CORPSE_PANIC    10

// Let the engine finish its own death processing (notetracks, drops) before the
// entity goes. Stock's giant-cleanup uses the same brief wait before Delete
// (zm_giant_cleanup_mgr.gsc:236-241).
#define TOD_CORPSE_SETTLE   0.05

// A FLUNG BODY'S LINGER. The Warrior's sword fling (_tod_warrior_melee) marks a launched body
// tod_bat_launched (the name is the retired baseball bat's); corpse_remove keeps it this long so the
// ragdoll is seen landing even on a full board. (The bat home run + the hoop left with the Map 1
// purge, 2026-10-04.)
#define TOD_BAT_LINGER      3.5         // a flung body's linger (s)

// PUBLIC — how many live zombies may stand at once for the CURRENT party size.
// 36 solo / 42 / 48 / 54 since 2026-09-28 (was 30 / 35 / 40 / 45), clamped both ends, PLUS
// TOD_RAMPAGE_AI_LIMIT_ADD while the breaker is thrown (46 / 52 / 58 / 58 under TOD_AI_LIMIT_CEIL). A fifth body cannot exist in ZM,
// but the clamp costs nothing and a 0-player frame (everyone disconnecting) must
// not return a negative.
function ai_limit_for_party()
{
	np = GetPlayers().size;
	if ( np < 1 )
		np = 1;
	n = TOD_AI_LIMIT_SOLO + ( np - 1 ) * TOD_AI_LIMIT_PER;
	if ( n > TOD_AI_LIMIT_MAX )
		n = TOD_AI_LIMIT_MAX;
	// RAMPAGE IS THE HARD MODE (v18.11, user 2026-09-07: "I want rampage to be
	// the difficult mode"). v18.11 held the pre-relief FLAT 45 here, which was
	// a 15-zombie step at solo and NO step at quad; v18.74 (user 2026-09-10:
	// "zombies alive at once jumps 10") makes it +10 over the party figure at
	// every size, so the step is the same for everyone and the player chose it.
	if ( IS_TRUE( level.tod_rampage_on ) )
		n = n + TOD_RAMPAGE_AI_LIMIT_ADD;
	if ( n > TOD_AI_LIMIT_CEIL )
		n = TOD_AI_LIMIT_CEIL;   // 2026-09-28: rampage 46 / 52 / 58 / 58
	// Reserve one companion actor per connected player, including a recharge.
	// The engine actor ceiling stays 60 and every stock spawn gate still applies.
	if ( isdefined( level.tod_partner_records ) ) n = n - np;
	return n;
}

// THE RAMP's round: the tower round, or the arena's fixed difficulty round mid-fight.
function ai_ramp_round()
{
	if ( isdefined( level.tod_arena_hp_round ) )
		return level.tod_arena_hp_round;
	if ( isdefined( level.round_number ) )
		return level.round_number;
	return 1;
}

// PUBLIC — 0 on round 1 .. 1 from the ramp's full round on (rampage: twice as fast).
function ai_ramp_frac( round )
{
	full = TOD_AI_RAMP_FULL_ROUND;
	if ( IS_TRUE( level.tod_rampage_on ) )
		full = TOD_RAMPAGE_AI_RAMP_FULL_ROUND;
	if ( round >= full )
		return 1;
	if ( round <= 1 )
		return 0;
	return ( round - 1 ) / ( full - 1 );
}

// PUBLIC — how many live zombies may stand at once THIS round (THE RAMP over the party cap).
function ai_limit_now()
{
	full = ai_limit_for_party();
	lo = int( full * TOD_AI_RAMP_START_FRAC + 0.5 );
	n = int( lo + ( full - lo ) * ai_ramp_frac( ai_ramp_round() ) + 0.5 );
	if ( n > full )
		n = full;
	if ( n < TOD_AI_RAMP_MIN )
		n = TOD_AI_RAMP_MIN;
	return n;
}

function init()
{
	// THE CAPS ARE SET HERE, not in the entry script, so the number and the
	// mechanism that makes it safe live in one file. Live values — stock's spawn
	// loop re-reads both every iteration (_zm.gsc:3735/3740), so this does not
	// need to beat any particular init to the punch.
	level.zombie_ai_limit    = ai_limit_now();
	level.zombie_actor_limit = TOD_ACTOR_LIMIT;

	// v18.11 — AND IT FOLLOWS THE PARTY. Polled rather than hooked on
	// connect/disconnect: stock re-reads the field on every spawn pass, so a 2 s
	// cadence is exact enough and needs no callback plumbing. This is the SAME
	// shape the retired coop_ai_limit() used, now living in the file that OWNS
	// the field — which is the whole reason that one had to be retired: two
	// writers on one field, and the looping one always wins.
	//
	// ONE WRITER, and it must stay that way. If a future change wants a
	// different concurrency during some phase, it belongs in
	// ai_limit_for_party() / ai_limit_now() (THE RAMP), not in a second thread.
	level thread ai_limit_watch();

	zm_spawner::register_zombie_death_event_callback( &on_zombie_death );
}

// [TOD_AI_CAP] (dev): one line whenever either cap moves - party, rampage or the allied reserve.
function cap_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_AI_CAP] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// Keeps level.zombie_ai_limit in step with the party. Writes only on a CHANGE so
// the common case is a compare, and so a debug read of the field is not a moving
// target every two seconds.
function ai_limit_watch()
{
	level endon( "end_game" );

	last = level.zombie_ai_limit;
	last_actor = level.zombie_actor_limit;
	for ( ;; )
	{
		wait 1;   // 2 -> 1 s (2026-09-28): the allied reserve below moves with every summon
		// Stock counts axis actors only. Reserve one allied slot per player
		// so enemy spawns cannot fill the engine pool underneath the companions.
		reserve = 0;
		if ( isdefined( level.tod_partner_records ) ) reserve = GetPlayers().size;
		// 2026-09-28: and every ALLIED actor standing right now (the Necromancer's thralls, hounds
		// and Manglers) - they share the engine's 64 with the horde, so the zombie gate shrinks by
		// exactly what they hold and the free slots elites and summons ask for are always there.
		allies = GetAITeamArray( "allies" ).size;
		reserve = reserve + allies;
		actor_lim = TOD_ACTOR_LIMIT - reserve;
		if ( actor_lim < 20 ) actor_lim = 20;
		level.zombie_actor_limit = actor_lim;
		lim = ai_limit_now();   // THE RAMP (2026-10-04): the party cap, grown into by round 30
		if ( lim != last || actor_lim != last_actor )
		{
			if ( lim != last )
				level.zombie_ai_limit = lim;
			cap_log( "CAP players=" + GetPlayers().size + " ai_limit=" + lim + " party_cap=" + ai_limit_for_party()
			       + " ramp_round=" + ai_ramp_round() + " actor_limit=" + actor_lim
			       + " allies=" + allies + " zombies=" + zombie_utility::get_current_zombie_count()
			       + " actors=" + zombie_utility::get_current_actor_count() + " free_actors=" + GetFreeActorCount()
			       + " rampage=" + IS_TRUE( level.tod_rampage_on ) );
			last = lim;
			last_actor = actor_lim;
		}
	}
}

// self = the killed zombie. One dispatch per death, synchronous with the rest of
// the death chain (points, luck, class-gun kill credit), so this must not block:
// it threads and returns.
function on_zombie_death( attacker )
{
	if ( !isdefined( self ) )
		return;

	// BOSSES OWN THEIR DEATHS. Every boss in this map is stamped is_boss +
	// acc_is_boss + acc_is_mini_boss (_tod_bosses.gsc:1010-1012, :1415-1417),
	// and the vendored packs run their own death sequences — a Panzer spawns a
	// death-anim clone and deletes itself. Deleting the body out from under that
	// is how you lose the animation, or worse. They are also a handful of
	// entities, not forty-five, so they are not what the cap is about.
	if ( IS_TRUE( self.is_boss ) || IS_TRUE( self.acc_is_boss ) || IS_TRUE( self.acc_is_mini_boss ) )
		return;

	self thread corpse_remove();
}

function bat_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_BAT] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// self = the corpse. A straight line: no loop, one conditional wait, and every
// step re-checks that the entity still exists — the engine can recycle a corpse
// underneath us at any time, and after Delete() nothing here holds a reference.
// linger: optional override of TOD_CORPSE_LINGER. v17.96 — elites pass a longer
// one so a Protector's fall / a Reaver's death swap can still be read before the
// body goes; the adaptive branch below still Ghosts immediately near the cap.
function corpse_remove( linger )
{
	// This callback is registered before Warrior's death callback. De-collide
	// immediately, then let ALL callbacks mark their ragdolls before deciding
	// whether actor pressure may hide one. Otherwise sword flings are invisible.
	self NotSolid();
	wait 0.05;
	if ( !isdefined( self ) ) return;
	if ( !isdefined( linger ) )
		linger = TOD_CORPSE_LINGER;
	// A flung body (the Warrior's sword fling marks tod_bat_launched) is in the air for
	// longer than the floor linger: give it TOD_BAT_LINGER.
	if ( IS_TRUE( self.tod_bat_launched ) && linger < TOD_BAT_LINGER )
		linger = TOD_BAT_LINGER;
	if ( IS_TRUE( self.tod_bat_launched ) )
		bat_log( "FLING_HOLD ent=" + self GetEntityNumber() + " seconds=" + linger + " actors=" + zombie_utility::get_current_actor_count() );
	// DE-COLLIDE ON THE DEATH FRAME, always, whatever the linger. A fresh body
	// that still blocks movement is the thing players actually feel — 45 of them
	// on a 160-wide staircase would be a wall. This is free and immediate.

	// ADAPTIVE: only spend the two seconds if the board can afford them.
	// Re-checked here rather than at death time because the interesting case is
	// a burst of kills — the first few bodies linger, and by the time the count
	// climbs the rest are going straight out.
	// A FLUNG BODY KEEPS ITS LINGER EVEN UNDER PRESSURE (v19.18): it is in
	// the air, and ghosting it on the death frame
	// would make every fling on a full board vanish mid-arc. There are only
	// ever a handful of them, so this cannot be what fills the pool.
	if ( IS_TRUE( self.tod_bat_launched ) || zombie_utility::get_current_actor_count() < ( TOD_ACTOR_LIMIT - TOD_CORPSE_PANIC ) )
	{
		wait linger;
		if ( !isdefined( self ) )
			return;   // the engine already recycled it — nothing to do
	}
	else
	{
		// Board is full: hide it now so the delete does not read as a body
		// blinking out of existence in front of the player.
		self Ghost();
	}

	wait TOD_CORPSE_SETTLE;
	if ( isdefined( self ) )
		self Delete();
}
