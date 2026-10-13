// =============================================================================
// _tod_main.gsc — orchestrator for the small stuff (proof-of-life banner,
// dev sandbox). Grows as [tod] systems are added; each new module gets its own
// file + a scriptparsetree line in zone_source/zm_tod2_cybercity.zone.
// =============================================================================

#using scripts\shared\callbacks_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_score;
#using scripts\zm\zm_tod2_cybercity\_tod_cyber_zombies;
#using scripts\zm\zm_tod2_cybercity\_tod_partners;
#using scripts\zm\zm_tod2_cybercity\_tod_cyber_elites;
#using scripts\zm\zm_tod2_cybercity\_tod_dealer_finale;   // THE DEALER (docs/199): the final boss
#using scripts\zm\zm_tod2_cybercity\_tod_class_cards;   // the class build cards (2026-09-27)
#using scripts\zm\zm_tod2_cybercity\_tod_arena;   // THE BATTLE ARENA (docs/185): floor-40 chamber -> the arena -> a card -> the top bay
#using scripts\zm\zm_tod2_cybercity\_tod_haven;   // THE HAVENS (docs/202): the safe zones' force-field domes (33% slower enemies, 33% less damage)
#using scripts\zm\zm_tod2_cybercity\_tod_doppelghast;   // THE DOPPELGHAST (docs/160 §9): the Fall's hunters, Hellbound's BO6 ghoul
// DEV-ONLY reach (dev_crown_test): the stock power entry point and the perk
// unpause it is always paired with, plus the crown's generated anchors. All
// three are behind level.tod_dev; with it false nothing here runs, but the
// #usings stay so the file always compiles either way. (The finale's gate went
// with the retired ending, 2026-10-05.)
#using scripts\zm\_zm_power;
#using scripts\zm\_zm_perks;
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;
#using scripts\zm\zm_tod2_cybercity\_tod_doors;

#using scripts\zm\zm_tod2_cybercity\_tod_zombie_speed;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_lights;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_anims;
#using scripts\zm\zm_tod2_cybercity\_tod_classes;
#using scripts\zm\zm_tod2_cybercity\_tod_upgrades;
#using scripts\zm\zm_tod2_cybercity\_tod_archer; // Retriever + grapple + fall immunity
#using scripts\zm\zm_tod2_cybercity\_tod_class_kit; // Warrior Bash + Gravity Smash, Breacher C4 + Thermite (Hellbound port, 2026-09-25)
#using scripts\zm\zm_tod2_cybercity\_tod_archer_bow; // bow draw -> damage (2026-09-25)
#using scripts\zm\zm_tod2_cybercity\_tod_athlete;     // ATHLETE (slasher slide/jump, domain 43)
#using scripts\zm\zm_tod2_cybercity\_tod_riotshield;  // RIOT SHIELD (universal recharging shield, domain 45)
#using scripts\zm\zm_tod2_cybercity\_tod_necro_skull;   // THE NECROMANCER's skull + Widow's = Burned Out (2026-09-26)
#using scripts\zm\zm_tod2_cybercity\_tod_necro_summon;  // its helpers (AIM) + the SOUL BOMB (2026-09-26)
#using scripts\zm\zm_tod2_cybercity\_tod_atmosphere;
#using scripts\zm\zm_tod2_cybercity\_tod_ammo_crate;   // buyable ammo at every breather (2026-08-24)
#using scripts\zm\zm_tod2_cybercity\_tod_rampage;      // RAMPAGE INDUCER: the opt-in hard mode (v14.20)
#using scripts\zm\zm_tod2_cybercity\_tod_killconfirm;  // ELITE KILL CONFIRM: red crosshair snap + ding, elites only (v18.96)
#using scripts\zm\zm_tod2_cybercity\_tod_secret;       // THE TEDDY BEAR SONG HUNT: the map's first secret (v18.96)
#using scripts\zm\zm_tod2_cybercity\_tod_base_sign;    // THE CYBERCITY SIGN over the plaza (docs/208, Nikolai's prop)
#using scripts\zm\zm_tod2_cybercity\_tod_class_terminal;   // THE CLASS TERMINAL (2026-10-01): the crown's class switch (tester kit, _tod_tester.gsh)
#using scripts\zm\zm_tod2_cybercity\_tod_ability_fx;   // THE ABILITY FEEDBACK (docs/203, 2026-10-02): clientfield lockstep with the .csc

#insert scripts\shared\shared.gsh;

#namespace tod_main;

function init()
{
	level endon( "end_game" );

	// Sprint-from-round-1 speed curve (registers its spawn callback; safe pre-blackscreen)
	tod_zombie_speed::init();
	tod_cyber_zombies::init();
	// Perk machine + PaP power-on glow auras (waits for the power flag itself)
	tod_perk_lights::init();
	// Individual vending machines retired; original BO6 animation is owned by Wunderfizz.
	// Class system (3 classes, base-arena select stations) + the upgrade tower
	tod_classes::init();
	tod_upgrades::init();
	// (CHAIN LUNGE removed 2026-08-24 — user: "it doesnt work". _tod_lunge.gsc
	// is off the zone; see the note at its old add_domain in _tod_upgrades.gsc.)
	// (The landing stumble is the ARCHER's alone - user 2026-09-26 "the slowdown
	// landing is only for archer" - so _tod_archer::stumble_watch owns the
	// jump_slowdownEnable dvar, not a global write here.)
	// Archer owns both offhand buttons; legacy monkey reconciliation is retired.
	tod_archer::init();
	tod_class_kit::init();
	tod_archer_bow::init();
	tod_athlete::init();
	// RIOT SHIELD (v16.63, domain 45): registers the Lv5 cyber shield as
	// equipment (the base shield is stock-registered through zm_usermap) and
	// installs an on_spawned reconcile + the break/recharge watchers. Same
	// ordering need as DISTRACTION: after zm_usermap::main().
	tod_riotshield::init();
	// THE NECROMANCER (2026-09-26): the skull's soul beam / torch / meter and
	// Widow's Wine = Burned Out. Registers its clientfields here (lockstep .csc).
	tod_necro_skull::init();
	tod_necro_summon::init();   // after the skull: it uses the skull's actor field
	// The neon city smog (thick at street level, clear by mid-tower)
	tod_atmosphere::init();
	// AMMO CRATE on each breather balcony (waits for the blackscreen itself)
	tod_ammo_crate::init();
	// RAMPAGE INDUCER (v14.20) — the opt-in hard mode. Spawns its station and
	// sets level.tod_rampage_on = false; every consumer treats the absent or
	// false field as normal difficulty, so ORDER DOES NOT MATTER here: the
	// speed curve, the elite directors and the spawn resolver all field-read it
	// with IS_TRUE and none of them run before this line anyway. Placed after
	// the crate purely to keep the world-object inits together.
	tod_rampage::init();
	tod_killconfirm::init();   // v18.96
	tod_ability_fx::init();    // docs/203: the ability feedback (both views) - before the class modules' casts can fire
	tod_secret::init();        // v18.96 (places the bears after the blackscreen)
	tod_base_sign::init();     // docs/208: the TOWER OF DOOM CYBERCITY sign (dark until the power, then a neon start)
	tod_partners::init();      // the AI companions (the Black Market's dealer gives each player one, docs/209)
	tod_class_terminal::init();   // 2026-10-01: the crown's class switch (TOD_TESTER_KIT in _tod_tester.gsh)
	tod_doppelghast::init();   // docs/160 §9: the BO6 audio table + counters; _tod_fall spawns the hunters
	tod_class_cards::init();   // the class build cards (2026-09-27): damage / armor / kill lanes + Shadowstep
	tod_cyber_elites::init();  // Normal-round Doppelgast/Mangler mix (separate from retired directors).
	tod_dealer_finale::init();   // docs/199: THE DEALER, the final boss (the crown-hall test spawn while TOD_DEALER_TEST_SPAWN is 1)
	tod_arena::init();         // docs/185: the Battle Arena (after the Mangler/Doppelghast inits it spawns through)
	tod_haven::init();         // docs/202: the safe zones (the domes boot with the power wave)
	// PARTY SIZE -> LUI. Started here (pre-blackscreen) so the dvar is never
	// unset the first time a menu reads it. See party_dvar_watch.
	level thread party_dvar_watch();
	level flag::wait_till( "initial_blackscreen_passed" );

	// Proof-of-life: the build is live and module init ran.
	welcome_banner();
	if ( IS_TRUE( level.tod_dev ) )
	{
		roster_setup = "[TOD_ROSTER] READY rev=20260924 dev=" + IS_TRUE( level.tod_dev ) + " god=" + IS_TRUE( level.tod_god )
			+ " maxed=" + IS_TRUE( level.tod_dev_maxed );
		/# PrintLn( roster_setup ); #/
	}

	// DEV MONEY, ON ITS OWN GATE (2026-09-07). It used to sit inside the
	// tod_dev block below, which meant "I want unlimited money" also bought
	// upgrades every round, a Panzer from round 3 and a TIER card on every
	// deal. Those are four different wishes and they now have two switches.
	// tod_dev still implies money, so no armed session loses anything.
	if ( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_dev_money ) )
		level thread dev_money_loop();

	// EVERY TOWER DOOR OPEN, on its own switch (user 2026-09-07: "can you open
	// up all the doors in dev mode?"). Same reasoning as the money split above:
	// tod_dev is a BUNDLE, and "I want to walk the tower" should not also buy an
	// upgrade every round and start Panzers at round 3. tod_dev still implies it,
	// so an armed tod_dev session loses nothing.
	if ( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_dev_doors ) )
		level thread dev_open_doors_harness();

	// TIER 3 + EVERY DOMAIN MAXED, on its own switch (user 2026-09-07: "when I
	// respawn into the map, give me all my abilities. I don't wanna have to
	// unlock them ... just give me my tier three weapon, with max upgrades").
	// [tod v19.9] OFF THE BUNDLE (user 2026-09-15: "In dev mode you need to remove
	// the max out classes you give me ... All i want is play the game normal with
	// god mode and unlimited money with all doors open"). tod_dev_maxed already
	// existed for exactly this; the bundle half is what handed out a tier-3 maxed
	// loadout nobody asked for. Arm tod_dev_maxed to get it back.
	if ( IS_TRUE( level.tod_dev_maxed ) )
		level thread dev_maxed_harness();

	if ( IS_TRUE( level.tod_dev ) )
	{
		// dev_crown_test() REMOVED AGAIN 2026-08-26, after the user's ending
		// retest passed. It is a throwaway harness for testing the top of the
		// map (open every door, force power through the stock entry point, open
		// the causeway gate, warp everyone to the terrace on spawn and on every
		// respawn) and it has now been written-then-deleted twice. Do NOT re-add
		// it inline or leave it dormant behind tod_dev; write it fresh if the
		// ending needs testing again. Recipe, so it is cheap to re-derive:
		//   tod_doors::dev_open_all_doors()          — flags AND slabs AND navmesh
		//   zm_power::turn_power_on_and_open_doors() — never poke "power_on" by
		//   zm_perks::perk_unpause_all_perks()         hand; it leaves perks paused
		//   tod_finale::gate_open()                  — else risers past it are cut
		//   callback::on_spawned( &warp )            — respawn too, not just spawn
		// Terrace centre is ( 0, 368, 19400 ), yaw 90, clear of the station.
		dev_print_sprint_dvars();   // v15 item 20 — see the function header
		// v16.1 — the slide/jump engine dvar family (jump_max_velocity etc.) as
		// the engine reports it, plus what _tod_athlete wrote. See its header.
		tod_athlete::dev_print_movement_dvars();
		// HARNESS #9 (2026-09-03, user: "Dont spawn me in at endless spire with
		// all perks. Just do a regular spawn at spawn on dev and god mode. On dev
		// mode the alter should be unlimited and all doors should be unlocked
		// already"): a PLAIN base spawn — no warp, no ascension, no perk grant —
		// with every buyable door open from the first second (flags, breather
		// unlocks, slabs, navmesh, retired prompts: tod_doors::dev_open_all_doors
		// does all four). Power is NOT flipped (the switch at the bottom still
		// works; the user asked for doors). The altar is already unlimited on
		// dev (station_depleted). NINTH WRITE; delete with the dev flags.
		// Moved onto tod_dev_doors below so it can be armed WITHOUT the rest of
		// the tod_dev bundle. Left here so an armed tod_dev session is unchanged.
		// level thread dev_open_doors_harness();   // HARNESS #9
		// (HARNESS #8, the Endless Spire spawn + hub warp pads, was deleted with
		// the spire on 2026-09-29.)
		// HARNESS #7 REMOVED 2026-08-31 for the publish build (the fog/spire
		// run: terrace warp on spawn AND on a 20s sweep for players already
		// in, all doors/power/perks/gate open, ascension-latched so it stopped
		// yanking spire players back). SEVENTH WRITE, SEVENTH REMOVAL.
		// Recipe delta vs the base recipe above, worth keeping because this
		// one cost a wasted playthrough: `callback::on_spawned` ALONE DOES NOT
		// WARP THE FIRST LIFE — this dev block runs after
		// `flag::wait_till("initial_blackscreen_passed")`, by which point every
		// player has already spawned, so the callback only ever catches
		// RESPAWNS. Any future warp harness must ALSO sweep the players who
		// are already in (loop them, SetOrigin, re-assert for ~20s so the
		// class draft cannot undo it).
		// HARNESS #6 REMOVED 2026-08-29 night (the spire verify run: terrace
		// warp on spawn/respawn until ascension + a dev summit-warp pad at the
		// spire arena; deleted for the v14.1 publish — sixth write, sixth
		// removal).
		// dev_crown_test() REMOVED AGAIN 2026-08-29 ~4:50am (harness #5, the
		// PaP-verification warp, removed with the same night's disarm). Five
		// writes, five removals — the recipe above stays current.
		// dev_crown_test() REMOVED AGAIN 2026-08-27 evening (harness #4, written
		// that afternoon for the road-ramp/finale test, deleted for the v12.15
		// publish). Four writes, four removals — the recipe above stays current;
		// write it fresh, never re-add it dormant.
	}

}


// (welcome text removed 2026-08-20 — user: no floaty text; the stub stays
// because init() still calls it as a proof-of-life marker.)
// PARTY SIZE -> LUI (2026-09-07). AetheriumStartMenu hides RESTART LEVEL and
// RESTART MAP in co-op (they reload the level under the host and drop the peer),
// and that gate needs a party count it can TRUST.
//
// ⚠️ Engine.GetPlayerCount() IS NOT THAT COUNT, and the way it looked like one
// is the lesson. The kit's Leave Game lane calls it — which is exactly why it
// was taken as proven — but THAT CALL SITE'S TWO BRANCHES ARE IDENTICAL:
//
//     if playerCount and playerCount <= 1 then  <disconnect>  else  <disconnect>  end
//
// so its return value has never decided anything and a wrong value was
// invisible there. Gating a real button on it removed the button in SOLO
// (user 2026-09-07: "I didnt see it in solo"), which is the first time anything
// in this map ever read that function's answer. A call nobody has watched
// DECIDE something is not a proven call, however many times it appears.
//
// GetPlayers().size is authoritative and server-side. It reaches Lua on the
// same dvar channel _tod_gameover uses for tod_go_active — that one IS proven,
// because the two-entry game-over menu has shipped on it since v9.24 and is the
// only thing that makes that menu appear.
//
// HOST-MACHINE ONLY, like every SetDvar here, and the failure direction is
// chosen: a co-op PEER reads "" and keeps the button. A peer pressing it drops
// only themselves; the HOST pressing it drops the whole party, and the host is
// the one seat this covers reliably. Solo also keeps the button if the read
// ever fails, so the worst case is the behaviour we had before the gate.
//
// Polled rather than event-driven: it must follow joins, leaves, disconnects
// and host migration, and one cheap compare a second covers all of them without
// a callback per lane. The dvar is only WRITTEN when the number moves.
function party_dvar_watch()
{
	level endon( "end_game" );

	last = -1;
	for ( ;; )
	{
		n = GetPlayers().size;
		if ( n != last )
		{
			last = n;
			SetDvar( "tod_party", "" + n );
		}
		wait 1;
	}
}

function welcome_banner()
{
}

// DEV ONLY (level.tod_dev hardcoded true + rebuild): keep everyone rich so
// doors/perks/box can be tested without farming.
// DEV ONLY (v15 item 20) — ARE THE SPRINT-TUNING DVARS REGISTERED IN RETAIL?
//
// ⚠️ THIS WAS WRITTEN ONCE ON 2026-09-01 AND VANISHED FROM THE FILE the same
// night (both the call and the body), during a pass another session made here.
// Restored. If it disappears again, suspect a concurrent edit rather than
// rewriting it a third time.
//
// User: "Can we make the skirmisher omni directional? He is able to run and gun
// but he stops running if you run at an angle." There is NO script lever for
// this — the whole T7 sprint surface is AllowSprint / IsSprinting /
// SetSprintDuration / SetSprintCooldown / SetClientPlayerSprintTime /
// SprintButtonPressed / SprintUpRequired, and none of them touch the direction
// cone. But Treyarch's own dvar string table (recovered from
// bin/cod2map64.exe) contains, verbatim:
//     player_sprintForwardMinimum — "The minimum forward deflection required to
//                                    maintain a sprint"
// which is exactly the knob. Setting engine movement dvars from GSC is stock
// practice: share/raw/scripts/zm/_zm.gsc SetDvars the sibling sprintLeap_enabled
// in the ZM path with no cheat gate.
//
// ⚠️ WHY A PRINT BEFORE A WRITE. SetDvar on an UNREGISTERED dvar silently
// creates a dead script dvar and no-ops — failure is INDISTINGUISHABLE FROM
// SUCCESS. The table was read out of a TOOL exe; the retail exe is packed and
// hashes dvar names, so scanning it proves nothing either way.
//
// HOW TO READ IT: a NUMBER means the dvar is live and the next build can set it.
// <UNREGISTERED> means the whole dvar lane is dead and the fallback is the
// SetMoveSpeedScale approximation (no sprint animation, but the gun stays up).
//
// STILL UNPROVEN EVEN IF THEY PRINT: co-op replication — this repo states that
// "host SetDvar never replicates to co-op peers", and sprint is client-predicted.
// Test in co-op, never solo only. And the dvar is GLOBAL: there is no per-player
// equivalent, so it would give omni-sprint to ALL FOUR classes, and a skirmisher
// who keeps sprinting while strafing has the GUN DOWN unless they own SPRINT FIRE.
function dev_print_sprint_dvars()
{
	names = array( "player_sprintForwardMinimum", "player_sprintStrafeSpeedScale",
	               "player_sprintSpeedScale", "player_strafeSpeedScale",
	               "player_backSpeedScale", "player_strafeAnimCosAngle" );
	for ( i = 0; i < names.size; i++ )
	{
		v = GetDvarString( names[ i ], "" );
		if ( v == "" )
			v = "<UNREGISTERED>";
		tod_quiet_print( "dvar " + names[ i ] + " = " + v );
	}
}

function dev_money_loop()
{
	level endon( "end_game" );
	for ( ;; )
	{
		players = GetPlayers();
		for ( i = 0; i < players.size; i++ )
		{
			player = players[ i ];
			if ( isdefined( player ) && isdefined( player.score ) && player.score < 100000 )
				player zm_score::add_to_player_score( 100000 - player.score );
		}
		wait 2;
	}
}

// ===========================================================================
// HARNESS #9 — DEV: EVERY DOOR OPEN AT START (2026-09-03). Waits for the
// door module's own ready flag (the buy triggers must exist
// before dev_open_all_doors retires them, or the doorways keep prompting),
// then opens all 53 through the ONE lane that also flags the zones, arms the
// breather elites and cuts the navmesh. No warp, no power, no perks.
function dev_open_doors_harness()
{
	level endon( "end_game" );
	for ( i = 0; i < 40 && !IS_TRUE( level.tod_doors_ready ); i++ )
		wait 0.5;
	if ( !IS_TRUE( level.tod_doors_ready ) )
	{
		IPrintLnBold( "DEV: doors never reported ready - not opened" );
		return;
	}
	tod_doors::dev_open_all_doors();
	IPrintLnBold( "DEV: every door is open" );
}

// EVERY PLAYER TO TIER 3 WITH EVERY DOMAIN AT ITS CAP. Nothing new is written
// here: tod_upgrades::dev_grant_maxed already does exactly this job through the
// real primitives (it stamps the floor high-water rather than waiving the gate,
// promotes, PaPs primary and sidearm, then walks every domain the player can
// reach to its cap and fires the real LUI sync). It simply had no live caller
// (its only one was the spire harness, deleted with the Endless Spire
// 2026-09-29).
//
// A tier-gated domain (set_tier_min) is refused below its tier, so the tier
// ladder must run BEFORE the domain max-out.
// dev_grant_maxed already does tier first — do not reorder it.
function dev_maxed_harness()
{
	level endon( "end_game" );

	// The draft lands on an ALREADY-SPAWNED player, so waiting on the class
	// being chosen is mandatory: granting before it would max a classless
	// player and skip every class-scoped domain.
	while ( !IS_TRUE( level.tod_class_select_done ) )
		wait 0.5;

	// Let the round-1 deal finish. Rewriting levels underneath an open card
	// panel means the panel is showing numbers that are already stale.
	wait 1;
	for ( i = 0; i < 120 && IS_TRUE( level.tod_upgrade_pause ); i++ )
		wait 0.25;

	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		if ( isdefined( players[ i ] ) && isplayer( players[ i ] ) )
		{
			players[ i ].tod_dev_maxed_done = true;
			line = "[TOD_DEV] MAXED start player=" + players[ i ] GetEntityNumber() + " class=" + players[ i ].tod_class;
			/#
			PrintLn( line );
			#/
			players[ i ] thread tod_upgrades::dev_grant_maxed( players[ i ] );
		}
	}
	wait 4;
	IPrintLnBold( "^2DEV: tier 3 + every upgrade maxed" );

	// LATE CLASSES (2026-09-26, user: "on dev mode, I shouldn't have any of my
	// abilities locked out ... this should apply to all the classes"). A co-op
	// drop-in gets its class after the pass above (tod_classes::assign_class),
	// so it would play un-maxed. Poll once a second (dev only) and max anyone
	// who has a class and was never granted.
	for ( ;; )
	{
		wait 1;
		players = GetPlayers();
		for ( i = 0; i < players.size; i++ )
		{
			p = players[ i ];
			if ( !isdefined( p ) || !isplayer( p ) || IS_TRUE( p.tod_dev_maxed_done ) || !isdefined( p.tod_class ) )
				continue;
			p.tod_dev_maxed_done = true;
			line = "[TOD_DEV] MAXED late player=" + p GetEntityNumber() + " class=" + p.tod_class;
			/#
			PrintLn( line );
			#/
			p thread tod_upgrades::dev_grant_maxed( p );
		}
	}
}

// ---------------------------------------------------------------------------
// v17.97 — DEV PRINTS ARE MUTABLE. level.tod_dev_quiet (set beside tod_dev in
// zm_tod2_cybercity::tod_resolve_dev_flags) silences every bottom-left IPrintLn
// in this file — screenshot sessions want dev + god with a clean HUD. Each
// print site's own tod_dev gate is unchanged; this is one extra gate under it.
// IPrintLnBold (real game toasts) is not routed here.
function tod_quiet_print( msg )
{
	if ( IS_TRUE( level.tod_dev_quiet ) )
		return;
	IPrintLn( msg );
}

function tod_quiet_print_to( msg )   // self = the player to print to
{
	if ( IS_TRUE( level.tod_dev_quiet ) )
		return;
	self IPrintLn( msg );
}
