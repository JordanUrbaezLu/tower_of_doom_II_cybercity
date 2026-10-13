// =============================================================================
// _tod_powerups.gsc — the map's custom powerup DROPS.
//
//   "tod_free_pap"  — the PERK BOTTLE drop. Instant, grabber-only, gated on
//     power. Grants a random perk the grabber does not already own.
//     NAME IS HISTORICAL: it granted a free Pack-a-Punch until 2026-08-21,
//     when the user reported (twice) that "the perk drop doesn't give me any
//     perks" — the drop uses the stock zombie_pickup_perk_bottle model, so it
//     READS as a perk drop and a PaP grant was invisible/confusing. The
//     powerup id is kept so the .csc include and the clientfield stay in
//     lockstep; only the grant changed. If every perk is already owned the
//     drop is still CONSUMED (a GiveMaxAmmo consolation) rather than left
//     stranded — on solo there is no teammate to leave it for.
//
// The OP weapon drop is the Gift of Death (Xmas Gun) — install_gift_of_death()
// overrides the stock Death Machine grant + installs fixed-shots damage. This
// module also reworks INSTA-KILL into a team-wide 3x damage window.
//
// (The admin-gun drop was removed on user order 2026-08-20.)
//
// Client half: _tod_powerups.csc (include + add for tod_free_pap).
// =============================================================================

#using scripts\shared\clientfield_shared;   // v13.6b: the ALXS idle-FX clientfield on the breather vendors
#using scripts\shared\flag_shared;   // power_on gate on the free-PaP drop
#using scripts\shared\laststand_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;

#using scripts\zm\_zm;
#using scripts\zm\_zm_perks;      // give_random_perk — the bottle grants a PERK
#using scripts\zm\_zm_powerups;
#using scripts\zm\_zm_score;      // breather Pack-a-Punch charges points
#using scripts\zm\_zm_utility;
#using scripts\zm\_zm_weapons;   // can_upgrade_weapon / get_upgrade_weapon (vendor stock lane)
#using scripts\zm\zm_cwpap;   // v13.12 — register_pap_machine: the vendors run the pack's own flow
#using scripts\zm\zm_tod2_cybercity\_tod_breather_data;   // GENERATED — lounge PaP anchors (v13)
#using scripts\zm\zm_tod2_cybercity\_tod_classes;   // is_class_primary (vendor: which lane)
#using scripts\zm\_zm_weapons;
#using scripts\zm\zm_tod2_cybercity\_tod_perk_roster;
#using scripts\zm\zm_tod2_cybercity\_tod_upgrade_ui;   // push_dmg_num (crosshair numbers)

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;
#insert scripts\zm\_zm_powerups.gsh;

// (No empty-name string precache here - 2026-10-05, LT-fix / LT-meteor: one never reaches the map's precache table,
// and the linker misreads every directive after it in the same file - the one in _tod_lucky.gsc cost that file all
// four effect precaches. These two models survived only because zm_cwpap.gsc precaches them too. The blank power-up
// hints below need none.)
#precache( "model", "p9_fxanim_zm_gp_pap_xmodel_off" );   // breather PaP vendor mesh, unpowered (ALXS pack, v13.6)
#precache( "model", "p9_fxanim_zm_gp_pap_xmodel" );       // its powered/animated twin (swapped at the flip)
// (v13.6b/c's anim grafts lived here between builds — RETIRED v13.12; the
// animtree, xanims and every show now run inside zm_cwpap itself, one code
// path for all five machines. See the tombstone below.)

// Gift of Death (Xmas Gun) grants on the Death Machine drop with FIXED
// shots-to-kill, round-independent: damage = health / shots, per archetype.
// 15 — HALF of stock N_POWERUP_DEFAULT_TIME (user 2026-08-25: "Make zombie blood
// last half as long as it currently does"). This is a BALANCE call, and the
// distinction matters for whoever tunes it next: the powerup was briefly cut to
// 10 earlier today for PERFORMANCE, on a rationale that turned out to be false
// (see the re-add note in init() — Zombie Blood never slowed the game; Time Warp
// did). It went back to 30, and this 15 is the deliberate balance choice on top
// of the corrected baseline, not a repeat of that mistake.
//
// The reason a shorter window earns its keep now: level.zombie_ai_limit went
// 24 -> 45 on 2026-08-25, so a window in which nothing dies fills a much bigger
// board than the 30 was originally tuned against.
#define TOD_BLOOD_SECS     15

// DROP RATES (user 2026-08-24: "We need to reduce the rate of pap drops cause
// they drop very often. I would say lets half the rate it currently is. And we
// need to drop the rate of death machine drop too. We can do half as well").
//
// HOW HALVING WORKS HERE, because it is not a weight table: stock picks a drop by
// shuffling level.zombie_powerups and taking the first entry whose
// func_should_drop_with_regular_powerups returns true — and on a false it picks
// AGAIN in a while(1) (_zm_powerups.gsc:377-386). So a should-drop that returns
// true only half the time gives that powerup exactly half its old share of
// drops, and the re-roll hands the other half to the rest of the pool. No stock
// edit, no weight plumbing, and the total drop RATE is unchanged — only the mix.
//
// The loop terminates because the always-drop powerups (insta-kill, double
// points, max ammo, nuke, carpenter) never refuse.
// HALVED AGAIN 2026-08-24 (user: "we need to fix is the amount of pap power up
// drops that drop. Lets reduce that probability again"). 50 -> 25, so the PaP
// now takes a QUARTER of the share it had before the first cut. Read the
// mechanism note below before changing it again: this is not a weight, it is a
// per-roll gate, and the re-roll hands the refused share to the rest of the
// pool — so 25 means "a quarter as often", not "25% of all drops".
// The DEATH MACHINE is deliberately untouched at 50: only PaP was named.
// THE SHARED SLOT (docs/219, 2026-10-05; user: the Wunderstrahl "shares the Gift of Death drop"): the Death Machine
// slot now hands out the Gift of Death OR the Wunderstrahl, 50/50, so big-weapon drops are no more common. Each
// half is a 25 gate (this define and _tod_wunderstrahl.gsc TOD_WS_DROP_PCT, LOCKSTEP; tools/wunderstrahl/
// test_wunderstrahl.js holds them equal and summing to the old 50), and neither drops while anyone holds either gun.
#define TOD_PAP_DROP_PCT      25   // free-PaP drop: a quarter of its former share
#define TOD_MINIGUN_DROP_PCT  25   // Death Machine (= the Gift of Death): HALF its slot - THE SHARED SLOT note above
#define XMAS_ZOMBIE_SHOTS  2     // normal zombie
// (v14.8's elite lanes - the Reaver's 6 and the hellhound's 3 fixed shots, x1.3
// buff - and the Panzer / Protector lanes in _tod_bosses retired whole with
// those enemies, 2026-10-05. A boss-flagged victim takes the Gift's raw damage.)
#define TOD_BREATHER_PAP_COST  5000   // stock PaP price

#namespace tod_powerups;

REGISTER_SYSTEM( "tod_powerups", &__init__, undefined )

function __init__()
{
	// FREE PACK-A-PUNCH (instant). register_powerup auto-includes the name
	// server-side; ORDER: every level.zombie_powerups[name].* setter (e.g.
	// can_pick_up_in_last_stand) MUST come AFTER add_zombie_powerup — the
	// struct it writes only exists post-add (live crash 2026-08-20).
	// DROP MODEL = the stock perk bottle (user 2026-08-20: the scaled Chaos
	// PaP-machine mesh read as an unrecognizable "frame" and its base-pivot
	// offset the visual from the grab origin — "couldn't grab it"). The bottle
	// is a clean, centered, reliably-grabbable powerup that still glows blue
	// on solo. (A PaP-machine-look drop needs a pivot-centered custom mesh —
	// revisit later.)
	zm_powerups::register_powerup( "tod_free_pap", &grab_free_pap );
	// NOT flagged prevent_pick_up_if_drinking (map 1's v19.53, ported 2026-10-04) - see
	// drinking_besides_powerup_gun(); grab_free_pap does the check itself.
	// POWER GATE (user 2026-08-21: "those drops should only start dropping
	// once power is on"). should_drop_free_pap replaces the stock always-drop.
	zm_powerups::add_zombie_powerup( "tod_free_pap", "zombie_pickup_perk_bottle", &"", &should_drop_free_pap, POWERUP_ONLY_AFFECTS_GRABBER, !POWERUP_ANY_TEAM, !POWERUP_ZOMBIE_GRABBABLE );
	zm_powerups::powerup_set_can_pick_up_in_last_stand( "tod_free_pap", 0 );

	// ---------------------------------------------------------------------
	// FREE PACK-A-PUNCH (user 2026-08-21) — its OWN drop again, now that a
	// real pickup model exists. Model `free_packapunch` = ZoekMeMaar's
	// purpose-built gold mini-PaP (pivot-CENTRED; the chaos machine mesh was
	// base-pivoted and read as a frame at drop scale). CREDIT ZoekMeMaar.
	// Power-gated for the same reason the perk bottle is: a free PaP before
	// the switch is thrown would skip the map's whole power gate.
	// ---------------------------------------------------------------------
	zm_powerups::register_powerup( "tod_pap", &grab_pap );
	zm_powerups::powerup_set_prevent_pick_up_if_drinking( "tod_pap", true );
	// HALVED 2026-08-24 — its own gate now, not the shared should_drop_free_pap.
	// The PERK BOTTLE (tod_free_pap, above) keeps the plain power gate: the user
	// asked about "pap drops", and the bottle is a random PERK, not a PaP.
	zm_powerups::add_zombie_powerup( "tod_pap", "free_packapunch", &"", &should_drop_pap, POWERUP_ONLY_AFFECTS_GRABBER, !POWERUP_ANY_TEAM, !POWERUP_ZOMBIE_GRABBABLE );
	zm_powerups::powerup_set_can_pick_up_in_last_stand( "tod_pap", 0 );

	// ---------------------------------------------------------------------
	// ZOMBIE BLOOD (user 2026-08-21) — model + vox from the NSZ powerup pack
	// (CREDIT NSZ). Grabber-only: for TOD_BLOOD_SECS the zombies stop
	// targeting you and you cannot be hurt. NO screen effect — the visionset
	// that used to be here was UNREGISTERED IN THIS MAP and a live bug; the long
	// note in zombie_blood_window() explains what it broke and what a real one
	// needs.
	//
	// RE-ENABLED 2026-08-25 — AND THE 2026-08-21 REMOVAL WAS A MISATTRIBUTION.
	// Worth recording properly, because the CHANGELOG states the old rationale as
	// fact and it does not hold.
	//
	// (It came back at its original 30s on 2026-08-25 and was then HALVED to 15
	// the same day on user instruction — "make zombie blood last half as long as
	// it currently does". TOD_BLOOD_SECS is 15; an earlier version of this
	// comment still said "AT ITS ORIGINAL 30s" and contradicted the #define four
	// screens up. Corrected 2026-08-26.)
	//
	// The drop was disabled in v8.5 citing "remove blood money or fix it - it
	// slows the whole game, not just zombies", with a rationale about a 30s
	// ignoreme window ballooning the horde and an "ignoreme repath storm"
	// tanking the server frame. Two things are wrong with that:
	//
	//   1. THE COMPLAINT WAS ABOUT TIME WARP (user 2026-08-25: "when I said that
	//      I was talking about the time warp drop not zombie blood"). The SAME
	//      v8.5 batch carries a Time Warp entry quoting the same sentence — one
	//      complaint applied to two systems, and the wrong one was removed.
	//   2. THE RATIONALE DOES NOT SURVIVE READING THE CODE. zombie_blood_window
	//      sets a flag, enables invulnerability and waits; the laststand guard is
	//      one waittill. No loop, no per-frame work, and ignoreme is a single
	//      field on the PLAYER — there is no repath storm.
	//
	// WHAT ACTUALLY FIXED IT is in the same batch: Logical's Time Warp pack was
	// calling player-only SetMoveSpeedScale on EVERY axis AI EVERY FRAME, bosses
	// included (custom-locomotion bosses stutter when their rate is stomped).
	// tod_warp_target() in scripts/zm/logical/powerups/_zm_powerup_timewarp.gsc
	// :163 now excludes bosses and non-zombies, and the loop re-asserts at 4 Hz
	// (wait 0.25, :204) instead of per frame. Verified still live 2026-08-25.
	//
	// THE ONE REAL CAVEAT: level.zombie_ai_limit went 24 -> 45 that day (and is
	// 30-45 by party size since v18.11, still 45 on rampage), so 30s in
	// which nothing dies fills a bigger board than it used to. That is a BALANCE
	// question for play, not the performance problem this was blamed for.
	// Shorten the window if it feels bad; do not shorten it "for frame time".
	// ---------------------------------------------------------------------
	// TRAY TIMER (live report 2026-08-26: "zombie blood doesn't show in the
	// bar"): the trailing three args put the window on the Aetherium powerup
	// tray via the STOCK timed-powerup lane — add_zombie_powerup registers the
	// 2-bit "toplayer" clientfield, and stock's powerup_hud_monitor drives it
	// every server frame from the per-player on/time vars that
	// zombie_blood_window() now maintains (grabber-only powerups read
	// player.zombie_vars and are gated on player._show_solo_hud — the exact
	// contract the stock Death Machine uses, _zm_powerup_weapon_minigun.gsc).
	// The clientfield name MUST match the .csc add AND the tray row in
	// AetheriumPowerupsContainer.lua ("tod_zombie_blood" in all three).
	zm_powerups::register_powerup( "tod_zombie_blood", &grab_zombie_blood );
	// NOT flagged prevent_pick_up_if_drinking (map 1's v19.53, ported 2026-10-04) - see
	// drinking_besides_powerup_gun(); grab_zombie_blood does the check itself.
	zm_powerups::add_zombie_powerup( "tod_zombie_blood", "zombie_blood", &"", &zm_powerups::func_should_always_drop, POWERUP_ONLY_AFFECTS_GRABBER, !POWERUP_ANY_TEAM, !POWERUP_ZOMBIE_GRABBABLE, undefined, "tod_zombie_blood", "zombie_powerup_zombie_blood_time", "zombie_powerup_zombie_blood_on" );
	zm_powerups::powerup_set_can_pick_up_in_last_stand( "tod_zombie_blood", 0 );

	// v17.99 — EVERY CUSTOM POWERUP THREW ON PICKUP (Workshop, Troy Terry
	// 2026-09-05: "weird error messages when i pick up power ups"). Stock's grab
	// (_zm_powerups.gsc:1104) runs zm_stats::increment_client_stat( name +
	// "_pickedup" ) -> globallogic_score::incPersStat -> `self.pers[ stat ] += 1`,
	// and only STOCK names are initPersStat'd (_zm_stats::player_stats_init:
	// nuke/insta_kill/full_ammo/...). For ours the pers slot is undefined, so the
	// add throws `pair 'undefined' and '1'` — the exact stack console_mp.log
	// carried 11 times (_globallogic_score <- _zm_stats <- _zm_stats <-
	// _zm_powerups). Our effect had already run (the _custom_powerups grab
	// callback is earlier in that function), but everything AFTER the throw in
	// stock's grab thread was skipped: the grab FX, the intro VO, and
	// powerup_delete_delayed + the "powerup_grabbed" notify (UNVERIFIED in game
	// whether the orb visibly lingered — the timeout thread still owns it).
	// Stock's own answer is the statless table (_zm_powerups::should_award_stat
	// reads level.zombie_statless_powerups): the whole stats block is skipped, so
	// no pers slot and no engine IncrementPlayerStat with a name the stats DDL
	// does not know. Keyed by NAME, so it does not care whether the vendored
	// modules (infiniteammo / timewarp) registered before or after this line.
	zm_powerups::powerup_set_statless_powerup( "tod_pap" );
	zm_powerups::powerup_set_statless_powerup( "tod_free_pap" );
	zm_powerups::powerup_set_statless_powerup( "tod_zombie_blood" );
	zm_powerups::powerup_set_statless_powerup( "infiniteammo" );   // scripts/zm/logical/powerups/_zm_powerup_infiniteammo.gsc
	zm_powerups::powerup_set_statless_powerup( "timewarp" );       // scripts/zm/logical/powerups/_zm_powerup_timewarp.gsc

	// BREATHER PACK-A-PUNCH vendors (see below) — one per rest balcony.
	level thread breather_pap_spawn();
	level thread crown_pap_clips();   // v13.9 — the ALXS prefab ships no collision
	level thread pap_power_hint();   // "REQUIRES POWER" copy while the switch is off
}

// ---------------------------------------------------------------------------
// BREATHER PACK-A-PUNCH (user 2026-08-22) — a standalone vendor per balcony
// ---------------------------------------------------------------------------
// WHY IT EXISTS: the CLASS TIER card requires the class gun Pack-a-Punched
// (tier_card_eligible), but when this was written the map's only PaP machine
// sat in the CROWN, above all 50 laps — unreachable during the climb where
// the gun is actually maxed. So the promotion could never fire (user: "I
// maxed out my Enfield and was never able to upgrade my class"). One machine
// per breather (floors 10/20/30/40) makes PaP reachable, which makes the
// tier ladder reachable.
//
// v14.35: the promotion now ALSO requires floor 10 (T2) / floor 30 (T3; 20 until 2026-09-02) —
// _tod_upgrades::tier_floor_ok. That is the same shape as this vendor
// placement, deliberately: the first two breathers are both the first two PaP
// machines and the two gate floors, so the normal climbing route is unchanged.
// What it closes is the FREE-PAP POWERUP, which sets tod_pap_owned wherever it
// drops and could hand a base-camped player a promotion with no doors bought.
//
// 2026-08-28 CORRECTION (same night, second pass): the crown PaP DOES still
// exist. An earlier claim that it was removed — briefly recorded here — came
// from grepping map_source for zm_pack_a_punch/packapunch, and the stock
// prefab matches NEITHER string: it is `vending_weapon_upgrade_spawnable.map`
// (gen_tower_map.js:4109, .map entity at (-480, 7913, 19392), hall west of
// the gate). VERIFY PaP-EXISTENCE AGAINST THE GENERATOR'S EMISSION, never by
// string-matching the output. So the hall holds TWO machines: the REAL
// Pack-a-Punch (west of the gate) and the personal UPGRADE STATION on the
// west wall wearing the chaos_pack_a_punch mesh (_tod_upgrades) — which is
// why "what does that pap do?" is such an easy question to ask up there.
// These four breather vendors exist because the crown machine is unreachable
// during the climb, exactly as the paragraph above says.
//
// WHY SCRIPT-SPAWNED AND NOT THE STOCK PREFAB — HARD-WON, DO NOT "SIMPLIFY":
// a SECOND stock `zm_pack_a_punch` zbarrier FATALS THE MAP LOAD. Stock
// _zm_pack_a_punch::spawn_init renames EVERY such zbarrier to the shared
// "vending_packapunch", then vending_weapon_upgrade() does a SINGULAR
// GetEnt("vending_packapunch") that errors with two or more. Map 1 paid for
// this exact lesson (its CHANGELOG, "Working 2nd Pack-a-Punch in Paradise":
// standalone custom vendor, never the stock zbarrier) and v9.16 re-paid it —
// 4 breather PaP prefabs in the .map and the map would not load. This vendor
// never carries that targetname, so the crown machine is untouched.
//
// HOW IT PACKS: NOT via the stock upgrade path. It latches
// player.tod_pap_owned — the SAME proven lane the free-PaP drop uses
// (grab_pap below) — and _tod_upgrades::reconcile_twin pulls the class gun to
// its `_up` form on its next 1s tick, building a variant name we KNOW the
// generator emitted. NO DIRECT CALL, DELIBERATELY: _tod_upgrades #usings THIS
// module, so importing it back would be a circular #using (the KB cycle rule).
function breather_pap_spawn()
{
	level endon( "end_game" );
	// This is threaded from __init__ (system registration), which runs EARLIER
	// than the tod module init() chain — the flag may not be defined yet, and
	// flag::wait_till on an undefined flag is not safe. Wait for it to EXIST
	// first, then for it to be set.
	while ( !( level flag::exists( "initial_blackscreen_passed" ) ) )
		wait 0.05;
	level flag::wait_till( "initial_blackscreen_passed" );

	// v13 — the PaP owns the lounge's WEST wall, facing east into the room
	// (it used to stand IN the entrance path at (-320,-470), its trigger 174u
	// from the ammo crate's with both costing 5000 — the reported wrong-buy).
	// Anchors are GENERATED (_tod_breather_data.gsc, the door-data no-drift
	// contract); the generator asserts every lounge trigger pair clears by
	// both radii + 64, so this machine can never crowd a neighbour again.
	zs = tod_breather_data::breather_zs();
	foreach ( z in zs )
		breather_pap_place( tod_breather_data::pap_org( z ), tod_breather_data::pap_trig( z ), tod_breather_data::pap_yaw() );
}

// v13.10 (user at the publish gate: "The pap at the crown had all these cool
// fx ... Can we please have that on all the paps? ... glwoing middle and top")
// — THE FX WERE ALREADY WIRED ON EVERY MACHINE; what the vendors were missing
// is the REKICK. The idle field is set once at the power flip, and the map-1
// lesson _tod_perk_lights' header records applies verbatim: "an FX spawned
// far from the viewer never becomes visible on approach". The crown got seen
// working; the four tower vendors sat beyond render reach when power came on
// and their glow never materialised for a climbing player. Fix = the same
// cure the perk glows ship: re-pulse the clientfield on the 0->1 edge the
// first time any player comes near the machine. Threaded on all FIVE
// machines (vendors at the flip, crown from its clips hook — a double pulse
// on the crown is harmless).
// ---------------------------------------------------------------------------
// v13.12 TOMBSTONE — breather_pap_use_loop / breather_pap_power_hint /
// vendor_pap_show / vendor_pap_lever / pap_fx_rekick are GONE. Every vendor
// interaction (trigger, hints incl. NEED_POWER, power model swap, idle show,
// purchase show, sounds, network-global cooldown, class-gun tier latch) now
// runs through the de-singularized zm_cwpap flow (user 2026-08-29: "just do
// it that way now") — one code path for the crown and all four vendors, via
// zm_cwpap::register_pap_machine in breather_pap_place. The refund-triage
// lesson from the old non-class lane lives on inside zm_cwpap ordering
// (can_upgrade is checked BEFORE the charge). The rekick died with the graft:
// the crown map-proven flow never needed one.
// ---------------------------------------------------------------------------

// v13.9 — the shared machine-collision row (see the comment at the vendor's
// call site). self-less helper: m = the machine script_model, clips stored on
// it for any future teardown (Hide != NotSolid — the QR invisible-wall rule).
function pap_place_clips( m )
{
	fwd = AnglesToForward( m.angles );
	offs = array( -32, 0, 32 );
	clips = [];
	for ( ci = 0; ci < offs.size; ci++ )
	{
		c = Spawn( "script_model", m.origin + VectorScale( fwd, offs[ ci ] ), 1 );
		c.angles = m.angles;
		c SetModel( "zm_collision_perks1" );
		c.script_noteworthy = "clip";
		c DisconnectPaths();
		clips[ clips.size ] = c;
	}
	m.tod_clips = clips;
}

// v13.9 — the CROWN machine gets the same row: the ALXS prefab ships model +
// trigger struct and NO collision (verified: walk-through, user report). The
// pack's model is singular by name, so this finds exactly one.
function crown_pap_clips()
{
	level endon( "end_game" );
	for ( i = 0; i < 40; i++ )
	{
		m = GetEnt( "pack_a_punch_model", "targetname" );
		if ( isdefined( m ) )
		{
			pap_place_clips( m );
			return;
		}
		wait 0.25;   // prefab models exist at init; the retry is pure paranoia
	}
}

// One vendor — v13.12: the machine model + collision, REGISTERED into the
// de-singularized zm_cwpap flow (user: "just do it that way now ... they all
// need to act as if they work together"). The pack's own code now runs this
// machine: its unitrigger, hints, power swap, idle show, purchase show, the
// network-global cooldown, and the class-gun tier lane — one code path for
// all five stations. Everything this module used to graft (use loop, power
// hint, show, rekick) is RETIRED below.
function breather_pap_place( model_org, trig_org, yaw )
{
	m = Spawn( "script_model", model_org );
	m.angles = ( 0, yaw, 0 );
	// v13.6 (user: "replace all pap machines with this new version"): the ALXS
	// CW/BO6 PaP mesh — the _off state at spawn; breather_pap_power_hint swaps
	// to the animated-on form at the power flip alongside its copy change.
	// Both models ride the alxs_cwpap zpkg (force-packed there). The full
	// animated system (zm_cwpap) is SINGULAR by design and lives on the crown;
	// these four keep our tod_pap_owned lane wearing the pack's machine.
	m SetModel( "p9_fxanim_zm_gp_pap_xmodel_off" );
	// SOLID SINCE v13.9 (user: "The new pap has no clip. I just walk through").
	// The old "deliberately not solid" stance was written for the small p7
	// wall-box; the CW cabinet is a real machine you expect to bump into, and
	// walking through it reads as a bug. Recipe = the upgrade stations'
	// proven one (_tod_upgrades:3711-3737, the Heavenly-Altar fix): THREE
	// zm_collision_perks1 script_models spaced +-32 along the mesh's local +X
	// (its wide axis, mapped by the entity yaw via AnglesToForward — do not
	// simplify to world axes), each DisconnectPaths'd per the navmesh rule.
	// The asset is stock-resident (station precedent: no zone line, no
	// precache). Machines back a wall, so over-cover is safe; zombies path
	// around the front like they do at every station.
	pap_place_clips( m );

	// v13.12 — the whole interaction belongs to zm_cwpap now. No jingle on
	// vendors (five overlapping music stings with unknown 2d routing; the
	// crown keeps it — flip the last arg to true to change that).
	zm_cwpap::register_pap_machine( m, trig_org, ( 0, yaw, 0 ), false );
}

// self = trigger. THE UNPOWERED STATE FOR THE FOUR BREATHER PACK-A-PUNCHES
// (live report 2026-08-25: "pack when power isnt on it doesnt say turn on power
// like other powered system").
//
// THESE FOUR ARE THE ONLY PACK-A-PUNCHES A PLAYER CAN REACH BEFORE THE FINALE,
// so they are the machines the report is about. Until now they carried ONE
// hint, stamped once at spawn, advertising the full buy card and a 5,000 price
// while power was off — and breather_pap_use_loop refused with nothing but a
// deny sound. The machine looked broken rather than unpowered.
//
// THE WORDING IS NOT FREE, AND THIS IS THE TRAP THAT MADE THE FIRST ATTEMPT AT
// THIS DEAD ON ARRIVAL. ZMCursorHintNew.lua routes hints by keyword:
//   isPAPHint (:205-213)  ->  "pack" AND "punch"  ->  the STATIC Pack-a-Punch
//                             card, which draws its own fixed title, blurb and
//                             cost and NEVER reads the hint text. Any power copy
//                             containing the machine's own name is therefore
//                             invisible by construction.
//   isPowerRequiredHint (:156-162)  ->  the literal substring
//                             "you must turn on the power first"  ->  the kit's
//                             dedicated Power Required card.
// So the line below deliberately does NOT name the machine, and DOES carry that
// exact sentence — which is also what every perk machine says, i.e. literally
// "like other powered systems".
//
// Edge-driven, not polled: two SetHintString calls per machine per game. Every
// distinct hint string costs a slot in the engine's trigger-string table, which
// is the config-string discipline the door price watcher documents.

// v13.6c — THE FULL PURCHASE SHOW ON EVERY VENDOR (user: "Okay can this be
// on every machine. DOe sit have to be crown only"). The pack's presentation
// is clientfield-driven PER ENTITY (all eight FX fields registered in BOTH
// VMs by zm_cwpap.gsc:51-58 / .csc:32-39 — parity verified), so the crown's
// buy sequence ports to the vendors verbatim: in-use anim, purchase FX,
// machine + lever + sting sounds, then back to idle. Cribbed exactly from
// zm_cwpap.gsc:127-147 (the sequence), :196-203 (the restore) and :318-341
// (the sounds), timings included (UPGRADE_FXANIM_TIME = 4).
// (HISTORY — this paragraph used to end with "ONE DELIBERATE DIFFERENCE: the
// crown hands the gun back after the show; the vendors keep our INSTANT
// take-and-give". That was TRUE ONLY OF THE v13.6c GRAFT and died with it in
// v13.12: every machine, the crown included, now runs zm_cwpap's own
// giveWeaponUpgraded / class-gun lane through register_pap_machine, so there
// is NO crown-vs-vendor behavioural difference left. Re-verified 2026-09-02
// when the user asked whether the crown PaP still "worked differently": the
// crown differs only in registering from the prefab's struct and keeping the
// jingle. Do not reintroduce a per-machine lane on the strength of this note.)


// self = trigger

// ---------------------------------------------------------------------------
// FREE PACK-A-PUNCH DROP (user 2026-08-21) — its own drop, own model
// ---------------------------------------------------------------------------
// WHY THIS DOES NOT USE THE STOCK UPGRADE PATH: the previous version called
// can_upgrade_weapon -> get_upgrade_weapon -> TakeWeapon/weapon_give, and it
// PaP'd the PISTOL fine but never the class guns (user report). Rather than
// keep guessing at which stock gate rejected the twins, we latch a flag and
// let _tod_upgrades::reconcile_twin do the swap — it builds
// `<primary><up_suffix><twin suffix>`, a name we KNOW the generator emitted,
// and it already owns the proven give->switch->ammo-delta->take-last order.
// Non-class weapons (the pistol) still take the stock path, which demonstrably
// works for them.
// self = the drop entity; player = the toucher. Return TRUE = NOT consumed.
function grab_pap( player )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return true;
	if ( player laststand::player_is_in_laststand() )
		return true;
	if ( isdefined( player.is_drinking ) && player.is_drinking > 0 )
		return true;
	// never PaP a temporary weapon-powerup gun (Gift of Death / Death Machine)
	if ( isdefined( player.zombie_vars ) && ( IS_TRUE( player.zombie_vars[ "zombie_powerup_minigun_on" ] ) || IS_TRUE( player.zombie_vars[ "zombie_powerup_tod_wunderstrahl_on" ] ) ) )
		return true;

	player PlayLocalSound( "free_packapunch_vox" );

	// CLASS GUN — the reliable lane. We only LATCH the flag; the swap itself
	// happens on the next tick of _tod_upgrades::body_systems_loop, which
	// already calls reconcile_twin() once a second.
	// NO DIRECT CALL, DELIBERATELY: _tod_upgrades #usings THIS module (for
	// max_ammo_clip_watch), so importing it back would be a circular #using —
	// the KB cycle rule. The <=1s latency is invisible next to the pickup
	// animation.
	// v10.30 (user 2026-08-25: "Free pap drop should pap the gun you have out").
	// MATCHED TO THE VENDOR. This used to pack the CLASS GUN first no matter
	// what was in hand, and only fell through to the held weapon once the class
	// gun was already packed — the same asymmetry the breather vendor had, and
	// the same surprise: grab the drop holding your sidearm and your PRIMARY
	// quietly got packed instead.
	//
	// ORDER, and why the fallbacks are in this order: the drop must NEVER be
	// stranded — on solo there is no teammate to leave it for, so every path
	// below ends in something being consumed.
	//   1. holding a NON-class weapon that can be upgraded -> pack THAT (stock path)
	//   2. otherwise, class gun not yet packed             -> latch it
	//   3. otherwise                                        -> consolation max ammo
	// Step 2 is what catches "holding an already-packed sidearm": rather than
	// waste the drop, it goes to the class gun, which is still the most valuable
	// thing it can do at that moment.
	w = player GetCurrentWeapon();

	held_is_class = ( isdefined( w ) && w != level.weaponNone
	                  && tod_classes::is_class_primary( player, w ) );

	// CLASS GUN — the reliable lane, taken when the class gun is what is in
	// hand. We only LATCH the flag; reconcile_twin does the swap within 1s.
	if ( held_is_class && tod_classes::pap_tier( player, w ) == 0 )
	{
		tod_classes::pap_first_grant( player, w );
		return;   // consumed
	}

	// NON-CLASS WEAPON IN HAND — the stock upgrade path, on the gun you are
	// actually holding.
	// OFFHAND GUARD (v14.59). can_upgrade_weapon() has NO offhand exclusion — it
	// asks only "is this weapon included, and does it have an .upgrade row". The
	// stock CSV gives `octobomb` an `octobomb_upgraded`, and GetCurrentWeapon()
	// can return an offhand (stock's own laststand code says so, mid-throw). So
	// while DISTRACTION (domain 41) handed out Li'l Arnies (v14.59-v16.48; it is
	// Cymbal Monkey-only since v16.49), grabbing a free-PaP drop mid-throw would
	// have TakeWeapon'd the octobomb and weapon_give'n an UNREGISTERED tactical,
	// which routes down the PRIMARY flow and eats a class gun. Silently, because
	// this map disables the too-many-weapons monitor. The guard belongs at this
	// call site regardless of that domain: nothing here ever wants to
	// Pack-a-Punch an offhand.
	if ( !held_is_class && isdefined( w ) && w != level.weaponNone
	     && !zm_utility::is_offhand_weapon( w ) && zm_weapons::can_upgrade_weapon( w ) )
	{
		up = zm_weapons::get_upgrade_weapon( w, false );
		if ( isdefined( up ) )
		{
			player TakeWeapon( w );
			up = player zm_weapons::weapon_give( up );
			if ( isdefined( up ) )
			{
				player GiveStartAmmo( up );
				player notify( "weapon_give", up );
				player SwitchToWeapon( up );
				return;   // consumed
			}
			// give failed — hand the original back rather than strand them
			player zm_weapons::weapon_give( w );
		}
	}

	// FALLBACK 2: the held weapon could not take it (already packed, or not
	// upgradable, or the give failed). Spend it on the class gun if that is
	// still dry — better than burning the drop on ammo.
	foreach ( primary in player GetWeaponsListPrimaries() )
	{
		if ( tod_classes::is_class_primary( player, primary ) && tod_classes::pap_tier( player, primary ) == 0 )
		{
			tod_classes::pap_first_grant( player, primary );
			return;   // consumed
		}
	}

	// FALLBACK 3: everything that could be packed already is — consolation ammo
	// PLUS +20% LUCK (v14.8, user 2026-08-30: "if a player already has a pap
	// gun but gets a pap drop they will get 20% luck"). Via the level pointer,
	// never a #using — powerups -> luck -> upgrades -> powerups is a cycle.
	if ( isdefined( w ) && w != level.weaponNone )
		player GiveMaxAmmo( w );
	if ( isdefined( level.tod_luck_dupe_fn ) )
		[[ level.tod_luck_dupe_fn ]]( player, "pap" );
	// consumed
}

// ---------------------------------------------------------------------------
// ZOMBIE BLOOD (user 2026-08-21) — the panic button
// ---------------------------------------------------------------------------
// For TOD_BLOOD_SECS the grabber is INVISIBLE to the horde and cannot be hurt.
// `player.ignoreme` is the stock lever the AI honours for target selection —
// far simpler and safer than the pack's own enemy-override hook, which would
// have needed a patch into the zombie targeting path.
// EnableInvulnerability covers the frame or two where an already-swinging
// zombie would otherwise land a hit.
function grab_zombie_blood( player )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return true;
	if ( player laststand::player_is_in_laststand() )
		return true;
	if ( drinking_besides_powerup_gun( player ) )
		return true;
	gift_grab_log( player, "tod_zombie_blood" );

	player thread zombie_blood_window();
	// consumed
}

// self = player
function zombie_blood_window()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	// Re-grabbing RESTARTS the window rather than stacking two threads that
	// would each try to clear the state (the second clear would end it early).
	self notify( "tod_blood_restart" );
	self endon( "tod_blood_restart" );

	self PlayLocalSound( "zombie_blood_vox" );
	self.ignoreme = true;
	self.tod_in_blood = true;
	self EnableInvulnerability();

	// HUD TRAY FEED (2026-08-26). Stock's powerup_hud_monitor reads these two
	// per-player vars every server frame for any grabber-only powerup whose
	// add_zombie_powerup carried a clientfield (ours does now, see __init__) —
	// but ONLY while player._show_solo_hud is true; that flag is the stock
	// gate on the whole per-player branch (weapon_powerup sets it the same way
	// for the Death Machine window). The countdown loop below replaces the old
	// plain `wait TOD_BLOOD_SECS` so the monitor sees the time shrink and runs
	// the expiring-flash stages itself.
	if ( !isdefined( self.zombie_vars ) )
		self.zombie_vars = [];
	self.zombie_vars[ "zombie_powerup_zombie_blood_on" ] = 1;
	self.zombie_vars[ "zombie_powerup_zombie_blood_time" ] = TOD_BLOOD_SECS;
	self._show_solo_hud = true;

	// NO VISIONSET HERE, AND THE ONE THAT USED TO BE HERE WAS A LIVE BUG
	// (2026-08-26). The line read:
	//
	//     self visionset_mgr::activate( "overlay", "zm_bgb_in_plain_sight", self, 2, 15, 2 );
	//
	// `zm_bgb_in_plain_sight` IS NOT REGISTERED IN THIS MAP. visionset_mgr
	// resolves by REGISTRATION, not by asset existence, so that alone is fatal.
	//
	// BE PRECISE, because the first version of this comment was WRONG and said
	// "the name was invented" (corrected 2026-08-26 after adversarial review).
	// THE NAME IS REAL — retail ships both the vision and the gum scripts:
	//     zone_source/all/assetlist/zm_common.csv:1831
	//         rawfile,vision/zm_bgb_in_plain_sight.vision
	//     zone_source/all/assetlist/zm_patch.csv:489-490
	//         _zm_bgb_in_plain_sight.gsc / .csc
	//
	// What is true is narrower, and still fatal: the mod tools ship only a STUB
	// BGB system (share/raw/scripts/zm/_zm_bgb.gsc is 17 lines of empty function
	// bodies, and no per-gum scripts exist at all), so whatever registers this
	// visionset at retail is in no tree we compile — and NOTHING in this usermap
	// calls visionset_mgr::register_info for it. A sweep of all 1223 script-like
	// files under the mod tools root finds the literal ONLY in this comment; the
	// single stock occurrence of the concept is the boolean
	// `entity.enemy.bgb_in_plain_sight_active` (shared/ai/zombie.gsc:393).
	//
	// So: the asset existing does not help us. activate() looks the name up in
	// level.vsmgr, and an unregistered name is simply absent from that table.
	//
	// WHY THAT WAS NOT MERELY COSMETIC: visionset_mgr::activate opens with
	//
	//     if ( level.vsmgr[type].info[name].state.should_activate_per_player )
	//
	// (visionset_mgr_shared.gsc:52) — an UNCONDITIONAL field dereference. With
	// the name unregistered, `.info[name]` is undefined and `.state` on undefined
	// is a script runtime error, so this thread DIED ON THIS LINE. Everything
	// below it never ran: the laststand guard never started, the wait never
	// elapsed, and zombie_blood_clear() NEVER FIRED — which left the grabber
	// `ignoreme = true` and INVULNERABLE for the rest of the match off a single
	// pickup. The powerup was a permanent god-mode toggle, not a 15s window.
	//
	// Zombie Blood is deliberately left with NO screen effect rather than a
	// substitute one: the mechanic is carried by ignoreme + invulnerability, the
	// grab already announces itself with zombie_blood_vox, and inventing a second
	// visionset name is exactly how this bug happened. If a visual is wanted
	// later it needs a REAL registration — visionset_mgr::register_info in an
	// __init__ plus the asset on a `visionset,` line in the .zone — and it must
	// be verified in game, not assumed.

	// Going down mid-window must not leave the player permanently ignored.
	self thread zombie_blood_laststand_guard();

	// Count the window down where the HUD monitor can watch it (a re-grab
	// kills this thread via tod_blood_restart and the fresh thread re-sets
	// the time to full — same restart contract as before).
	while ( IS_TRUE( self.tod_in_blood ) && self.zombie_vars[ "zombie_powerup_zombie_blood_time" ] > 0 )
	{
		// KEEP-ALIVE — the same doctrine as the zombie-gait sweep, and for the
		// same reason: a one-shot write gets undone by a system that owns the
		// field on a timer.
		//
		// STOCK OWNS .ignoreme THROUGH A REFCOUNT, AND CLEARS IT 2 SECONDS AFTER
		// A REVIVE (N_REVIVE_VISIBILITY_DELAY, _zm_laststand.gsc:42, applied at
		// :1374/:1472) — that pending decrement writes the boolean
		// UNCONDITIONALLY (_zm_utility.gsc:3852). So: go down, get revived, grab
		// a blood drop inside the next 2s, and the decrement fires mid-window and
		// kills 13 of the 15 seconds of invisibility while invulnerability stays
		// on. Reads to the player as "zombie blood did nothing". Reachable SOLO
		// too — Quick Revive's auto_revive arms the same delay.
		//
		// The IS_TRUE( tod_in_blood ) term in the loop head is LOAD-BEARING:
		// zombie_blood_clear() sets tod_in_blood undefined, so a mid-window down
		// stops this re-assert instead of forcing ignoreme = true onto a crawler
		// and stealing stock's last-stand reference.
		self.ignoreme = true;
		// THE TRAY GATE TOO (v17.47). Stock's minigun window end
		// (_zm_powerups.gsc:1895/:1934 — the Gift of Death rides it) writes
		// _show_solo_hud = false unconditionally, and that is code we do not
		// own. The Logical packs' matching writes were REMOVED the same day;
		// this re-assert covers the one writer left, so a Death Machine ending
		// mid-window no longer blanks the blood icon while you are still ignored.
		self._show_solo_hud = true;
		wait 0.05;
		self.zombie_vars[ "zombie_powerup_zombie_blood_time" ] = self.zombie_vars[ "zombie_powerup_zombie_blood_time" ] - 0.05;
	}

	self zombie_blood_clear();
}

// self = player
function zombie_blood_laststand_guard()
{
	self endon( "disconnect" );
	self endon( "tod_blood_restart" );
	level endon( "end_game" );

	self waittill( "player_downed" );
	// THIS GUARD OUTLIVES ITS OWN WINDOW. Nothing notifies it when the 15s
	// expires normally, and its endons are only disconnect / tod_blood_restart /
	// end_game — so it stays parked here and fires on an UNRELATED down rounds
	// later, stripping stock's last-stand ignoreme (making the player instantly
	// targetable the moment they are revived) along with the rest of the blood
	// state. Latent since the powerup was written; it got sharper on 2026-08-26
	// when zombie_blood_clear() gained the HUD-timer writes.
	//
	// tod_in_blood is set on entry and cleared by zombie_blood_clear() on EVERY
	// exit path, so it is the exact, future-proof test — better than adding a
	// "blood over" notify and a fourth endon, because it stays correct against
	// any future exit that calls clear() directly. (Until now the field had two
	// writes and zero readers repo-wide, which is the tell that this is what it
	// was always meant for.)
	if ( !IS_TRUE( self.tod_in_blood ) )
		return;   // window already ended — this down is not ours to clear
	self zombie_blood_clear();
}

// self = player. Idempotent — safe to call from either exit path.
function zombie_blood_clear()
{
	if ( !isdefined( self ) )
		return;
	// DON'T STOMP STOCK'S REFCOUNT. Last stand does not own .ignoreme directly —
	// it owns a COUNT (_zm_laststand.gsc:201 set_ignoreme(true) ->
	// zm_utility::increment_ignoreme, _zm_utility.gsc:3833) and derives the
	// boolean from it. A hard `false` here clears the boolean while the count is
	// still 1, which destroys the 2-second post-revive visibility grace
	// (N_REVIVE_VISIBILITY_DELAY) — the revived player becomes targetable the
	// instant they stand up. Recompute from the count exactly as stock does at
	// _zm_utility.gsc:3852.
	//
	// FIELD SPELLING IS STOCK'S OWN TYPO — `ignorme_count`, no second "e"
	// (_zm_utility.gsc:3835, verified by eye 2026-08-26). Misspelling it yields
	// undefined and silently reverts to the old hard-false with NO compile error
	// and no lint catch.
	//
	// DELIBERATELY NOT increment_ignoreme/decrement_ignoreme: clear() can run
	// twice for one window (the laststand guard and the loop exit), and a double
	// decrement would steal stock's own last-stand reference — trading a
	// cosmetic bug for a real one. This recompute is idempotent.
	self.ignoreme = ( isdefined( self.ignorme_count ) && self.ignorme_count > 0 );
	self.tod_in_blood = undefined;
	// ANOTHER OWNER MAY STILL HOLD THE SHIELD (map 1's bug review F15, ported 2026-10-04).
	// The card-deal world pause (tod_pause_invuln), the Black Market spin and its exit grace,
	// the crown's class terminal and its grace and the Dealer's house shield all
	// EnableInvulnerability on their own account, and the blood
	// window's countdown can expire inside any of them. Their releases already ask
	// tod_upgrades::pause_invuln_held_elsewhere (which reads tod_in_blood) the other way
	// round; this is the mirror, read inline because _tod_upgrades #usings this module.
	if ( !IS_TRUE( self.tod_pause_invuln )
	     && !IS_TRUE( self.tod_spin_locked ) && !IS_TRUE( self.tod_spin_grace )
	     && !IS_TRUE( self.tod_cls_term_locked ) && !IS_TRUE( self.tod_cls_term_grace )
	     && !IS_TRUE( level.tod_house_shield ) )
		self DisableInvulnerability();
	// (no visionset to deactivate — see the note in zombie_blood_window)

	// Take the tray icon down with the window.
	if ( isdefined( self.zombie_vars ) )
	{
		self.zombie_vars[ "zombie_powerup_zombie_blood_on" ] = 0;
		self.zombie_vars[ "zombie_powerup_zombie_blood_time" ] = 0;
	}
	// Drop the solo-HUD gate only if no OTHER grabber-only window still needs
	// it — the Death Machine (= Gift of Death) rides the stock minigun vars,
	// and zeroing the flag mid-window would blank ITS tray icon. The Logical
	// packs' solo_hud_fix loops re-assert the flag themselves, so they never
	// need protecting here. IS_TRUE, not a raw read: this map never inits the
	// minigun var on players who haven't grabbed one (the v8.4 boot-fix rule).
	if ( !( isdefined( self.zombie_vars ) && ( IS_TRUE( self.zombie_vars[ "zombie_powerup_minigun_on" ] ) || IS_TRUE( self.zombie_vars[ "zombie_powerup_tod_wunderstrahl_on" ] ) ) ) )
		self._show_solo_hud = false;
}

// ---------------------------------------------------------------------------
// MAX AMMO ALSO FILLS THE CLIP (user 2026-08-21)
// ---------------------------------------------------------------------------
// Stock full_ammo calls GiveMaxAmmo per weapon, which refills the RESERVE
// only — grab it mid-magazine and you still have to reload. The stock powerup
// notifies each affected player "zmb_max_ammo" (_zm_powerup_full_ammo.gsc
// :79), so we ride that instead of overriding the powerup: top every primary's
// clip to clipSize WITHOUT charging the reserve (the reserve was just filled).
// Threaded per player from tod_main's spawn hook.
function max_ammo_clip_watch()   // self = player
{
	// RESPAWN LATCH. This is registered via callback::on_spawned, and
	// callback::callback THREADS every registered func on every dispatch — while
	// a co-op bleed-out respawn dispatches "on_player_spawned" TWICE (_zm.gsc
	// :3338 in spectator_respawn, then _globallogic_spawn.gsc:465 in spawnPlayer,
	// which the custom path returns into with no early exit). With only
	// disconnect/end_game endons the thread is per-life immortal on a player
	// entity that is never deleted, so every respawn added TWO more copies —
	// 60-120 stale sweeps on one player over a long endless run.
	// The latch goes in the FUNCTION, not at the registration site, so it covers
	// any future caller. Same shipped idiom as _tod_uniques, _tod_runandgun and
	// _tod_luck; the field survives death because the ZM player entity is never
	// deleted. Do NOT use callback::remove_on_spawned — it deregisters for EVERY
	// player, not just the respawner.
	if ( IS_TRUE( self.tod_max_ammo_clip_on ) )
		return;
	self.tod_max_ammo_clip_on = true;

	self endon( "disconnect" );
	level endon( "end_game" );

	for ( ;; )
	{
		self waittill( "zmb_max_ammo" );
		wait 0.05;   // let the stock GiveMaxAmmo pass finish first

		if ( !isdefined( self ) || !IsAlive( self ) )
			continue;

		// DISTRACTION (_tod_distraction, domain 41) rides this same settle wait:
		// its decoy grenade is opted OUT of stock full_ammo and gains exactly +1
		// per grab instead. Called through a level pointer, not a #using — that
		// module imports _tod_upgrades, which imports THIS one, so a direct
		// import would close the cycle. Guarded, so the module being absent
		// degrades to "no top-up" rather than to a crash.
		if ( isdefined( level.tod_distract_max_ammo ) )
			self [[ level.tod_distract_max_ammo ]]();

		weapons = self GetWeaponsListPrimaries();
		foreach ( w in weapons )
		{
			if ( !isdefined( w ) || w == level.weaponNone )
				continue;
			if ( w.clipSize <= 0 )
				continue;   // melee / equipment
			if ( self GetWeaponAmmoClip( w ) < w.clipSize )
				self SetWeaponAmmoClip( w, w.clipSize );
		}
	}
}

// Drop gate — the perk bottle only enters the rotation once the power is
// on ("power_on" is a FLAG, never a bool field; flag::get is the read).
// Guarded with flag::exists because this can be polled before _zm's flag init.
// ---------------------------------------------------------------------------
// PACK-A-PUNCH: "REQUIRES POWER" COPY (user 2026-08-25)
// ---------------------------------------------------------------------------
// "It was because power was off. Lets make sure it has power offline copy. It
// didnt and I kept trying to pap when power wasnt on."
//
// Stock DOES set a hint for this — _zm_pack_a_punch.gsc:354 does
// SetHintString( &"ZOMBIE_NEED_POWER" ) — and on this map it renders as
// NOTHING, so the machine is silently inert and reads as broken. It cost a
// full round-trip of "PaP is broken again" to find that out.
//
// WHY NOT JUST SUPPLY THE STRING: localizedstrings/zm_aetherium.str cannot
// define it. The T7 string compiler auto-prepends the FILENAME to every
// REFERENCE key (see that file's FILENOTES), so a key written as
// ZOMBIE_NEED_POWER becomes ZM_AETHERIUM_ZOMBIE_NEED_POWER and the stock
// reference is unreachable from our file. A literal hint string is the only
// lever, which is the same thing the ammo crate and every buyable door do.
//
// SAFE AGAINST STOCK OVERWRITING IT: stock's pap_trigger_hintstring_monitor
// does `level waittill( "Pack_A_Punch_on" )` BEFORE its update loop
// (_zm_pack_a_punch.gsc:151-170), so while power is off nothing else writes the
// trigger's hint. The moment power lands we stop touching it and stock's
// monitor owns the string again — we deliberately do not set a powered hint,
// because stock's is the one that knows the weapon and the cost.
function pap_power_hint()
{
    level endon( "end_game" );

    // Same exists-poll breather_pap_spawn() uses above, and for the same reason:
    // this module's __init__ runs early enough that even
    // "initial_blackscreen_passed" may not be created yet. Most tod modules can
    // call wait_till on it bare; the two threads started from THIS __init__
    // cannot, which is precisely the distinction the note at the top of
    // breather_pap_spawn draws.
    while ( !( level flag::exists( "initial_blackscreen_passed" ) ) )
        wait 0.1;
    level flag::wait_till( "initial_blackscreen_passed" );

    // WAIT FOR THE FLAG TO EXIST BEFORE READING OR WAITING ON IT.
    //
    // THIS LINE CRASHED THE MAP (2026-08-25, shipped for one build):
    // "cannot cast undefined to bool ... scripts/shared/flag_shared.gsc".
    // flag::get() returns self.flag[ name ], which is UNDEFINED for a flag that
    // does not exist yet, and flag::wait_till() is a `while ( !get( name ) )` —
    // so waiting on a not-yet-created flag negates undefined and fatals the
    // server script. It presented as random because it is a race: only when this
    // thread reaches the wait before _zm's flag init does.
    //
    // "power_on" is a STOCK flag and this module only READS it — nothing here
    // creates a flag. should_drop_free_pap() below has carried the same
    // flag::exists guard, and the same reason, since it was written; that
    // precedent was there to follow and this did not follow it.
    //
    // The combined `exists( x ) && get( x )` form used in _tod_finale and
    // _tod_perk_lights is fine and was NOT the bug here — the bug was waiting on
    // a flag without checking it exists at all.
    while ( !( level flag::exists( "power_on" ) ) )
        wait 0.1;

    if ( level flag::get( "power_on" ) )
        return;   // powered before we got here — leave stock's hint alone

    trigs = GetEntArray( "pack_a_punch", "script_noteworthy" );
    if ( trigs.size == 0 )
        return;

    // THIS PASS USED TO WRITE "^5PACK-A-PUNCH^7 - ^3REQUIRES POWER^7" HERE AND
    // IT WAS WRONG TWICE OVER (audit 2026-08-25):
    //
    //   1. IT COULD NEVER BE READ. ZMCursorHintNew.lua:205-213 routes any hint
    //      containing "pack" AND "punch" to the STATIC Pack-a-Punch card, which
    //      renders its own fixed title/blurb/cost and never looks at the text.
    //      The words were drawn nowhere, in any state.
    //   2. IT WAS A REGRESSION. Stock ships &"ZOMBIE_NEED_POWER" on this
    //      trigger, and THAT string already routes to the kit's Power Required
    //      card (isPowerRequiredHint, :156-162). Overwriting it replaced a
    //      working card with an invisible one.
    //
    // So the string is gone and stock's own is left alone. The pass now only
    // fixes the CURSOR ICON, which is still worth doing.
    //
    // NOTE ON REACH: this targets script_noteworthy "pack_a_punch", which stock
    // stamps on the ONE zbarrier-derived trigger — the CROWN PaP
    // (vending_weapon_upgrade_spawnable, gen_tower_map.js:4109; a 2026-08-28
    // claim that it had been removed was a grep-term artifact — the prefab
    // name contains neither "packapunch" nor "zm_pack_a_punch"). That machine
    // sits at the top of the 50-floor climb, so in practice nobody stands at
    // it with the power off. The reachable machines are the four breather
    // vendors, handled by breather_pap_power_hint() above.
    foreach ( t in trigs )
    {
        if ( !isdefined( t ) )
            continue;
        t SetCursorHint( "HINT_NOICON" );
    }

    // Nothing to hand back any more — we never took the string. Left as a
    // no-op wait so the thread still ends on the flag rather than lingering.
    level flag::wait_till( "power_on" );
}

function should_drop_free_pap()
{
	if ( !( level flag::exists( "power_on" ) ) )
		return false;
	return ( level flag::get( "power_on" ) );
}

// The FREE-PAP drop's gate: the power rule above, then a coin flip that halves
// its share of the rotation (user 2026-08-24 — see TOD_PAP_DROP_PCT).
function should_drop_pap()
{
	if ( !should_drop_free_pap() )
		return false;
	return ( RandomInt( 100 ) < TOD_PAP_DROP_PCT );
}

// The DEATH MACHINE drop's gate — installed OVER stock's by install_gift_of_death
// so whatever stock decides still applies, with our coin flip on top.
function tod_should_drop_minigun()
{
	if ( isdefined( level.tod_minigun_stock_should_drop )
	  && ![[ level.tod_minigun_stock_should_drop ]]() )
		return false;
	// THE SHARED SLOT (docs/219): never while anyone holds the Wunderstrahl, the slot's other half
	foreach ( p in GetPlayers() )
		if ( isdefined( p.zombie_vars ) && IS_TRUE( p.zombie_vars[ "zombie_powerup_tod_wunderstrahl_on" ] ) )
			return false;
	return ( RandomInt( 100 ) < TOD_MINIGUN_DROP_PCT );
}

// THE GIFT OF DEATH NO LONGER BLOCKS THE PERK BOTTLE AND ZOMBIE BLOOD (map 1's v19.53,
// ported 2026-10-04, docs/208; its user: "when you are holding the Gift of Death you cannot
// grab drops ... pack-a-punch is one that you shouldn't be able to grab but there are other
// ones like perk drops or zombie blood that you should").
// STOCK COUNTS THE POWERUP GUN AS A DRINK: zm_powerups::weapon_powerup calls
// increment_is_drinking for the whole Gift of Death (the Death Machine lane it rides), and
// the grab loop refuses every powerup flagged prevent_pick_up_if_drinking while
// is_drinking > 0 - so the perk bottle and Zombie Blood were dead for the gun's whole window.
// Those two drop the stock flag and ask this instead: a drink OTHER than the powerup gun's
// own one (a real perk bottle, PaP taking the weapon, a revive). Neither touches the held
// weapon: the bottle is zm_perks::give_perk (SetPerk, no bottle animation), Zombie Blood is
// flags + invulnerability. The PaP drop keeps the stock flag AND grab_pap's own minigun_on
// refusal - it would upgrade the temporary gun. has_powerup_weapon is stock's own marker,
// set and cleared beside the increment / decrement.
function drinking_besides_powerup_gun( player )
{
	if ( !isdefined( player.is_drinking ) )
		return false;
	n = player.is_drinking;
	if ( IS_TRUE( player.has_powerup_weapon ) )
		n = n - 1;
	return ( n > 0 );
}

// dev-only: a drop taken while the powerup gun is out (the lane above)
function gift_grab_log( player, name )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) || !IS_TRUE( player.has_powerup_weapon ) )
		return;
	line = "[TOD_POWERUP] ms=" + GetTime() + " GIFT_GRAB player=" + player GetEntityNumber() + " drop=" + name + " is_drinking=" + player.is_drinking;
	/#
	PrintLn( line );
	#/
}

// self = the drop entity; player = the toucher. Return TRUE = NOT consumed
// (the grab loop keeps polling — the drop stays for someone who can use it).
// Runs synchronously in the grab poll: the upgrade happens THIS frame so the
// held weapon can't change between check and apply (the ZoekMeMaar Mule-Kick
// dupe was exactly that race).
function grab_free_pap( player )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return true;
	if ( player laststand::player_is_in_laststand() )
		return true;
	if ( drinking_besides_powerup_gun( player ) )
		return true;
	gift_grab_log( player, "tod_free_pap" );

	// A PERK the grabber does not already own — FROM THE MACHINES THIS MAP
	// ACTUALLY SELLS. NOT stock give_random_perk (live bug, 3-player report
	// 2026-08-29): that helper draws from ALL of level._custom_perks, and this
	// map #using's stock perk modules it does not sell — MULE KICK
	// (_zm_perk_additionalprimaryweapon, kept for its clientfield: the Death
	// Perception HUD icon BORROWS hudItems.perks.additional_primary_weapon,
	// see _tod_perk_electric_cherry's icon note) and stock ELECTRIC CHERRY
	// (kept for the tesla-FX pipeline). A drop that rolled Mule Kick lit the
	// borrowed field — so the player saw the DEATH PERCEPTION icon appear,
	// got no outlines, and the DP machine still sold the perk (they never had
	// that specialty). tod_give_random_map_perk below draws only from perks
	// with a live vending trigger in the .map. Returns undefined when every
	// sellable perk is held — DON'T strand the drop (solo has no teammate to
	// save it for): consume it and refill ammo as the consolation, the same
	// rule the old PaP grant used.
	got = player tod_give_random_map_perk();
	if ( !isdefined( got ) )
	{
		// Every sellable perk owned — consolation ammo PLUS +10% LUCK (v14.8,
		// user 2026-08-30: "if they get a perk bottle with max perks they
		// will get 10% luck"). Same pointer lane as the PaP dupe above.
		w = player GetCurrentWeapon();
		if ( isdefined( w ) && w != level.weaponNone )
			player GiveMaxAmmo( w );
		if ( isdefined( level.tod_luck_dupe_fn ) )
			[[ level.tod_luck_dupe_fn ]]( player, "perk" );
	}
	// consumed (no return value) — stock plays zmb_powerup_grabbed + hides it
}

// self = player. Free bottles and Wunderfizz share the explicit nine-perk roster.
// This stays valid without physical zombie_vending triggers and preserves stock
// perk hooks, owned/paused exclusions and the free solo Quick Revive exemption.
function tod_give_random_map_perk()
{
	return tod_perk_roster::give_random( self );
}


// ---------------------------------------------------------------------------
// GIFT OF DEATH (Xmas Gun) — the Death Machine drop grants it, with FIXED
// shots-to-kill (2 zombie / 10 Rogue Protector / 30 Panzer), round-independent.
// Called from main() AFTER zm_usermap::main() (stock minigun __init__ seeded
// level.zombie_powerup_weapon["minigun"]) and BEFORE tod_main::init() (so our
// actor callback registers ahead of _tod_upgrades::upgrade_damage_cb).
// ---------------------------------------------------------------------------

function install_gift_of_death()
{
	// Redirect the stock Death Machine grant (grant + timed-take + last-stand-
	// take all read this one level field) to the Gift of Death (base form).
	if ( GetWeapon( "xmas_gun" ) != level.weaponNone )
		level.zombie_powerup_weapon[ "minigun" ] = GetWeapon( "xmas_gun" );

	// DEATH MACHINE DROP RATE HALVED (user 2026-08-24). Stock's own gate is
	// CAPTURED rather than replaced — the same latch idiom as
	// level.tod_mechz_stock_damage_func — so minigun_no_drop's "somebody is
	// already holding one" rule keeps working and we only add the coin flip.
	if ( isdefined( level.zombie_powerups ) && isdefined( level.zombie_powerups[ "minigun" ] ) )
	{
		level.tod_minigun_stock_should_drop = level.zombie_powerups[ "minigun" ].func_should_drop_with_regular_powerups;
		level.zombie_powerups[ "minigun" ].func_should_drop_with_regular_powerups = &tod_should_drop_minigun;
	}

	zm::register_actor_damage_callback( &xmas_fixed_shots_cb );

	// INSTA-KILL rework (user 2026-08-20: "insta kill should grant all players
	// 3x damage output, different than base"). The stock insta_kill_powerup
	// checks level.insta_kill_powerup_override and runs it INSTEAD of setting
	// the one-shot flag — so ours grants a team-wide 3x damage window. The mult
	// is read at the ZOMBIE final-damage sites only: upgrade_damage_cb (all
	// player weapons) + xmas_fixed_shots_cb (the Gift of Death). BOSSES are
	// deliberately EXEMPT — their damage is fixed/round-independent by design
	// (Gift of Death 2/10/30 shots; the mechz wrap runs last and would rescale
	// anything set upstream). level.tod_dmg_mult defaults to 1.
	level.tod_dmg_mult = 1;
	level.insta_kill_powerup_override = &instakill_3x_override;
}

// Runs INSTEAD of the base insta-kill (stock threads it from insta_kill_powerup
// with (drop_item, player)). Shows the stock insta-kill HUD icon + timer but
// grants 3x damage for the duration rather than the one-shot. Re-grab restarts
// the window via the tod_instakill_<team> notify/endon.
function instakill_3x_override( drop_item, player )
{
	team = player.team;
	level notify( "tod_instakill_" + team );
	level endon( "tod_instakill_" + team );

	level thread zm_powerups::show_on_hud( team, "insta_kill" );   // icon + countdown
	level.tod_dmg_mult = 3;
	// (3X announce removed 2026-08-20 — the tripled crosshair numbers ARE the tell)
	wait N_POWERUP_DEFAULT_TIME;
	level.tod_dmg_mult = 1;
}

// Level actor-damage callback — NORMAL ZOMBIES only: a boss-flagged victim
// returns -1 (the chain continues with the Gift's raw damage).
// self = the AI taking damage. Return -1 = not our concern (chain continues).
function xmas_fixed_shots_cb( inflictor, attacker, damage, flags, meansofdeath, weapon, vpoint, vdir, sHitLoc, psOffsetTime, boneIndex, surfaceType )
{
	if ( !isdefined( weapon ) || !isdefined( weapon.name ) || !IsSubStr( weapon.name, "xmas_gun" ) )
		return -1;   // not the Gift of Death — let the rest of the chain run
	// Boss-flagged victims (the Mangler, the Doppelghast, the Dealer) take the
	// Gift's raw damage: the Map One fixed-shot elite lanes (the Panzer and
	// the Protector in _tod_bosses, the Reaver and the hellhound here) retired
	// whole with those enemies, 2026-10-05.
	if ( IS_TRUE( self.is_boss ) || IS_TRUE( self.acc_is_boss ) || IS_TRUE( self.acc_is_mini_boss ) )
		return -1;
	// No free damage on the frozen horde during an upgrade pick.
	if ( IS_TRUE( level.tod_upgrade_pause ) )
		return 0;
	// Guard 0/spurious events + same-frame dedupe (verify 2026-08-20): keeps it
	// exactly 2 shots even if a direct impact + splash ever co-fire one frame.
	if ( !isdefined( damage ) || damage <= 0 )
		return -1;
	now = GetTime();
	if ( isdefined( self.tod_xmas_hit_ms ) && self.tod_xmas_hit_ms == now )
		return 1;
	self.tod_xmas_hit_ms = now;

	hp = ( isdefined( self.maxhealth ) ? self.maxhealth : self.health );
	// INSTA-KILL 3x window multiplies output (level.tod_dmg_mult; default 1).
	dmult = ( isdefined( level.tod_dmg_mult ) ? level.tod_dmg_mult : 1 );
	final = int( ( hp / XMAS_ZOMBIE_SHOTS ) * dmult ) + 1;   // 2 hits from full, any round
	if ( isdefined( attacker ) && isplayer( attacker ) )
		attacker tod_upgrade_ui::push_dmg_num( final, false );   // crosshair number parity
	return final;
}
