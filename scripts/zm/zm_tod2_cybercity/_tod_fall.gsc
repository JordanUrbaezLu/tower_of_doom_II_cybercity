// =============================================================================
// _tod_fall.gsc — THE FALL: Tower of Doom II's opening (docs/160).
//
// User 2026-09-23: "all the players will spawn up in the crown room, and
// players will get overrun and ... it's going to be about $5,000 to open up
// the gate ... supposed to build anxiety and players just really want to get
// out of there because they're going to die and once everyone's out of the
// crown the doors will lock up ... they actually need to go down instead of
// up ... zombies kind of come in sprinting right off the bat, and then once
// that door is open and everyone's past that door that door locks up and the
// game actually slows down and it really starts then."
//
// User 2026-09-24 (docs/160 §10): "players pick their class and then can walk
// around for 20 seconds and then there is a spinning alarm at the top of the
// crown that starts a siren and this is when the flood comes in. Zombies will
// move at max sprint for default max sprint in bo3. Pap will be here and the
// alter will be here as well."
//
// THE TIMELINE THIS MODULE RUNS:
//   blackscreen -> power on -> the class draft (world frozen) -> the round-1
//   card deal (still frozen) -> THE CALM: TOD_FALL_CALM_SECS of unpaused quiet
//   with nothing spawning (the stock spawner's own "spawn_zombies" flag is
//   held clear from init) -> THE FLOOD: the alarm beacons light and spin, the
//   siren winds up and LOOPS until the 5000 gate is bought, the flag is set and the horde rises at
//   BO3's full sprint -> THE HUNTERS' clock starts (Doppelghasts from
//   TOD_FALL_HUNT_AFTER_SECS, then every TOD_FALL_HUNT_EVERY_SECS) -> the gate
//   is bought -> every living player is out -> THE SEAL.
//
// WHAT THIS MODULE OWNS — and only this:
//   * THE CROWN PHASE FLAG. level.tod_fall_phase is TRUE from init until the
//     seal. Two readers, both field reads (no import either way):
//       _tod_zombie_speed::rate_for_round  -> every zombie at EXACTLY 1.0 (BO3's sprint)
//       _tod_endless_rounds::tod_spawn_delay -> the crown trickle (x0.7)
//     When the flag drops, the 1.5 s keep-alive sweep re-asserts the round
//     curve (round 5 reads ~0.85x) and the next round rollover restores the
//     stock-derived trickle. That is the "game actually slows down".
//   * THE FLOOD HOLD. Stock _zm::round_spawning waits on flag "spawn_zombies"
//     before EVERY spawn (share/raw/scripts/zm/_zm.gsc:3753 — "added ability
//     to pause zombie spawning"). init() clears it before the first spawn can
//     happen; flood() sets it. Rounds cannot advance meanwhile (THE TWIST
//     waits for the round's zombies to SPAWN), so the party walks a quiet
//     round 1. Players are never frozen for it — that is the point.
//   * THE ALARM. Thirty Blender-authored rotating red fixtures: all twelve
//     hall pillars, central pendant, sixteen crown points and the apex.
//     _tod_crown_alarm owns the models, red spot FX and off/on state. This
//     module retains the trigger, original 30-second siren and seal edge.
//   * THE POWER. On from the first frame (turn_power_on_and_open_doors +
//     perk_unpause_all_perks, the dev harness's proven pair — never poke the
//     flag by hand). The crown's Pack-a-Punch and the altar are the whole
//     point of staying ("highly skilled players can stay there, rack up some
//     money and then pack a punch"); the CW PaP waits on power_on, and so does
//     every perk the party meets on the way down. The plaza switch is vestigial.
//   * THE SEAL. The Fall gate itself is a row of _tod_doors (generated flag
//     `tod_fall`, dest "the Causeway", FALL_GATE_COST party-scaled) — the
//     buy, the hint and the open are the door contract's. Once the flag is
//     set this module waits until EVERY LIVING PLAYER is outside the hall
//     (in_hall — the doorway counts as inside, a downed teammate inside
//     holds it open), holds TOD_FALL_SEAL_GRACE seconds of empty hall,
//     checks nobody is standing in the slab's box, and re-solidifies the
//     slab: Show + Solid + DisconnectPaths, the proven door-reseal contract.
//     Then: the hall's zone stops spawning (is_spawning_allowed = false is
//     the field stock's spawner reads per zone), the hall's respawn group is
//     locked again (spawn_points[i].locked, the field stock's selector
//     reads), and every ordinary zombie still inside is deleted — a body
//     behind a path-severed slab would hold an actor slot for the rest of
//     the match with no way to a player. Elites are left to
//     tod_boss_stuck_watch, which relocates them with an entrance.
//   * THE LIGHTING-STATE LOG (docs/162 T1). [TOD_LIGHTSTATE] lines at the
//     blackscreen, after power_on and on every spawn: the level's script state
//     and each player's own. Paired with the two test lights the generator
//     places on the hall's west wall (LIGHT_TEST_T1). Read docs/162 10 §7.3.
//
// WHAT IT DOES NOT DO. Rounds keep advancing once the flood is in — THE
// TWIST is untouched, so the longer a party farms the hall the harder the
// descent starts (that is the anxiety). No floor/tier/music logic lives
// here: those modules read the DESCENT defines of their own (docs/160).
//
// DIAGNOSTICS: [TOD_FALL] INIT / POWER / HOLD / CALM / FLOOD / SIREN / ALARM /
// OPEN / EMPTY / SEAL / HUNT lines and [TOD_LIGHTSTATE] in the console log.
// Both print WITHOUT the dev flag for the first playtests (the user tests
// dev-OFF builds) — zero TOD_FALL_LOG and TOD_LIGHTSTATE_LOG before a publish.
// =============================================================================

#using scripts\codescripts\struct;
#using scripts\shared\callbacks_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\util_shared;
#using scripts\shared\ai\zombie_utility;
#using scripts\zm\_zm_utility;
#using scripts\zm\zm_tod2_cybercity\_tod_doors;         // force_open_by_flag: the gate opens free at init (TOD_FALL_GATE_OPEN)
#using scripts\zm\_zm_perks;
#using scripts\zm\_zm_power;
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;     // GENERATED: hall/gate/siren anchors
#using scripts\zm\zm_tod2_cybercity\_tod_perk_lights;    // set_glow: the todPerkGlow client FX lane (index 11 = the alarm light)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;   // derez_burst / play_sound_at_origin (host-based, proven)
#using scripts\zm\zm_tod2_cybercity\_tod_doppelghast;    // THE HUNTERS (docs/160 §9): spawn_hunter / hall_spot / alive_count
#using scripts\zm\zm_tod2_cybercity\_tod_mangler;        // THE RAMP: spawn_at / live_manglers
#using scripts\zm\zm_tod2_cybercity\_tod_power_terminal;   // docs/208: THE GRID TERMINAL is the power switch's look (spawn_at / boot)
#using scripts\zm\zm_tod2_cybercity\_tod_crown_alarm;    // the physical alarm beacons (init/start/stop) - MOVED UP 2026-09-26: a #using after #precache/#define killed the compile ("No generated data", build 7)
#using scripts\shared\laststand_shared;           // player_in_hall skips a downed player (2026-10-04)

#insert scripts\shared\shared.gsh;

// (the stock switch models: retired from this script by docs/208 - the Grid Terminal is the power switch;
// _tod_power_terminal precaches its pieces, the zone keeps the stock pair for the plaza's vestigial prefab)
#precache( "model", "tod_alarm_button_stand" );   // THE ALARM BUTTON (2026-09-28), zone xmodel lines beside the switch's
#precache( "model", "tod_alarm_button_cap_on" );
#precache( "model", "tod_alarm_button_cap_off" );
#precache( "fx", "electric/fx_elec_sparks_directional_orange" );

// THE CALM AND THE FLOOD (user 2026-09-24, docs/160 §10). CALM_SECS of
// UNPAUSED time from the end of the round-1 deal (the draft and the deal both
// freeze the world; a frozen second does not count), then the alarm.
#define TOD_FALL_CALM_SECS   20                 // the TIMED calm — only when TOD_FALL_LEVER is 0 (the A/B)
// THE SIREN IS A TRUE LOOP (2026-09-29, user: "The Alarm does not stay on forever like it should.
// It stops at some point and we need it to loop ... Should stop once door is bought"). Three rows
// in tod_bosses.csv, all 3D and Pauseable, cut from the 30 s nuclear-siren master by
// tools/fall_siren/make_siren_clips.py (re-run it, never hand-edit the clips): a wind-up one-shot,
// a seamless 20.6 s LOOPING row (two whole wail cycles, the seam measured clean), and a wind-down
// one-shot for the moment the gate is bought. The loop is the host's entity loop sound, so it
// survives an ESC pause, a busy mix and a late joiner; the old 30 s one-shot re-played on a
// game-time timer went silent whenever a pause outlasted it (the 13:03 run, 2026-09-29).
#define TOD_FALL_SIREN_START       "tod_fall_siren_start"   // wind-up, 7.05 s (fades out over its last XFADE)
#define TOD_FALL_SIREN_LOOP        "tod_fall_siren_loop"    // LOOPING, 20.64 s
#define TOD_FALL_SIREN_STOP        "tod_fall_siren_stop"    // wind-down, 3.2 s
#define TOD_FALL_SIREN_LOOP_AT     6.7    // s into the wind-up where the loop takes over (LOCKSTEP: make_siren_clips.py prints LOOP_START)
#define TOD_FALL_SIREN_XFADE       0.35   // s: the wind-up fades out while the loop fades in (LOCKSTEP: XFADE in make_siren_clips.py)
#define TOD_FALL_SIREN_STOP_SECS   3.2    // s: the wind-down's length; the host lives until it ends (LOCKSTEP: STOP_SECS)
#define TOD_FALL_SIREN_STOP_FADE   0.25   // s: the loop fades under the wind-down's first moments

// THE LEVER (user 2026-09-24: "a lever at the top of the Throne in the crown,
// where players will press it to try to activate the tower ... the game doesn't
// start until the players activate that ... we can use the power switch for
// now"). The calm is no longer a timer: the party spawns to the intro track,
// the hall is silent, and NOTHING spawns until someone pulls the lever. The
// lever is the stock power switch's two models spawned by script on the
// sanctuary's top step in front of the reredos (the hall's throne end), with
// stock's own flip: handle RotateRoll -90 + zmb_switch_flip, then the sparks
// and zmb_turn_on (_zm_power::electric_switch, verbatim). On the pull the
// beacon spins and the siren winds up AT ONCE; the spawns release
// TOD_FALL_LEVER_LEAD_SECS later (the siren's wind-up), the Doppelghast clock
// counts from the pull. The plaza switch is still the vestigial prefab.
// Anchors: GENERATED lever_org()/lever_yaw() in _tod_crown_data.gsc. The
// prompt reads "activate the power" on purpose: ZMCursorHintNew routes that
// to the POWER SWITCH card. 0 = the timed calm above, lever never spawned.
#define TOD_FALL_LEVER           1
// THE LEVER IS THE POWER (user 2026-09-25: "the jump pad, Quick Revive ...
// shouldn't be working until the power is on"): power_on() moved from the
// blackscreen to flood() — the pull (or the timed calm) turns the grid on,
// stock's own way (turn_power_on_and_open_doors + perk_unpause_all_perks), so
// everything that already waits on "power_on" waits for the lever: the perks
// (solo Quick Revive is stock's exception: powered from round 1), the crown
// Pack-a-Punch, the teleporters, the item shops, and the jump pad
// (_tod_jumppad::refuse_reason). THE GATE IS OPEN AT INIT (TOD_FALL_GATE_OPEN):
// the lever stands in THE OVERLOOK beyond the hall gate, and there are no
// points to buy a door with before the first zombie, so the 5000 gate is
// opened free at init by _tod_doors::force_open_by_flag; the seal still
// closes it behind the party (Show + Solid + DisconnectPaths, unchanged).
// 2026-09-25, AFTER THE TWO SWITCHES: the user, "when I was in the crown the
// door was open, it should have been closed ... there needs to be a trigger, it
// should be 5,000". The alarm switch is inside the hall now, so the zombies it
// brings are the money for the gate: 0 = the generated 5000 buy door (party-
// scaled like every door, _tod_doors::door_price). 1 = open free at init.
#define TOD_FALL_GATE_OPEN       0
#define TOD_FALL_LEVER_LEAD_SECS 10                 // pull -> spawns released (the siren winds up over ~10 s)
#define TOD_FALL_LEVER_HINT      "Hold ^3[{+activate}]^7 to activate the power"
// TWO SWITCHES (user 2026-09-25, after the first play of the overlook: "there
// should be a switch to start the alarm. But that should be inside the
// crown"). 2026-09-28: THE ALARM BUTTON (a red button on a stand, the hall centre; GENERATED alarm_button_org/_yaw) replaced the ALARM SWITCH that stood on the sanctuary top step (GENERATED
// alarm_switch_org/_yaw): it cuts the intro, spins the beacon, starts the
// siren and releases the spawns — the game starts there. THE POWER SWITCH
// (lever_org/_yaw, the overlook's rail) arms only AFTER the alarm and turns the
// grid on: perks, PaP, shops, teleporters, the jump pad, and the veil's clear
// (level.tod_fall_power_ms). The zombies the alarm brings are the money for
// whatever stands between the hall and the power. Same stock models and flip.
// The prompt says THE ALARM (a TOD_NOUNS entry -> the default card); the power
// keeps "activate the power" (-> the POWER SWITCH card).
// THE POWER WAVE (user 2026-09-25: "once power's on things will light up
// dynamically ... as it's turning on"; picked A WAVE DOWN THE TOWER). The map
// boots in Radiant State 2 with EVERY light off (gen_tower_map.js BLACKOUT:
// lights are lightingstate1 only, the world has no glow). The power switch
// plays a coloured light on each floor TOP DOWN (GENERATED wave_orgs/wave_fx:
// each floor's own light spot in its district colour) over TOD_FALL_WAVE_SECS,
// holds, then util::set_lighting_state( 0 ) turns every baked light on at once
// and the wave's hosts go. One knob per symptom: too slow/fast = WAVE_SECS; the
// full light arrives too late = WAVE_HOLD_SECS.
#define TOD_FALL_WAVE_SECS       12
#define TOD_FALL_WAVE_HOLD_SECS  1.5
#define TOD_FALL_WAVE_FADE_SECS  1.0
#define TOD_FALL_ALARM_HINT      "Hold ^3[{+activate}]^7 ^5THE ALARM^7 - wake the tower"
// THE GRID TERMINAL (docs/208) replaced the stock switch's body + handle here (TOD_FALL_LEVER_BODY/_HANDLE).
#define TOD_FALL_LEVER_SPARKS    "electric/fx_elec_sparks_directional_orange"   // stock's switch_sparks; zone fx line + precache below
#define TOD_FALL_LEVER_FLIP_SND  "zmb_switch_flip"
#define TOD_FALL_LEVER_ON_SND    "zmb_turn_on"
#define TOD_FALL_LEVER_TRIG_R    48
#define TOD_FALL_LEVER_TRIG_H    72
#define TOD_FALL_LEVER_TRIG_OUT  28                 // trigger centre this far in FRONT of the body (the prefab's own trigger sits y -24..-5)
#define TOD_FALL_LEVER_TRIG_LIFT 24
// THE ALARM BUTTON (user 2026-09-28: "replace [the alarm switch] with a red button on top of a stand in the centre
// of the crown. Then players will press the button"). Blender-authored (tools/alarm_button): the stand is static,
// the cap is its own model so it presses DOWN; cap_on glows red while armed, cap_off is the pressed dark red.
// LOCKSTEP: CAP_Z = tools/alarm_button/01_author.py CAP_Z; the stand's clip (37 tall) is cut by the generator.
#define TOD_FALL_BUTTON_STAND    "tod_alarm_button_stand"
#define TOD_FALL_BUTTON_CAP_ON   "tod_alarm_button_cap_on"
#define TOD_FALL_BUTTON_CAP_OFF  "tod_alarm_button_cap_off"
#define TOD_FALL_BUTTON_CAP_Z    38.2
#define TOD_FALL_BUTTON_PRESS    1.3      // cap travel on the press
#define TOD_FALL_BUTTON_TRIG_R   64       // any side of the stand
#define TOD_FALL_BUTTON_TRIG_H   56
#define TOD_FALL_BUTTON_TRIG_LIFT 40      // trigger origin ABOVE the stand's clip (a use trigger whose origin sits in a solid never prompts)
#define TOD_FALL_SPAWN_FLAG  "spawn_zombies"    // stock's own spawner gate (_zm.gsc:1604 init true, :3753 waited per spawn)

// THE HUNTERS (user 2026-09-24: "In this room after some time if players dont
// leave after 1:30 dopplghast will start to spawn in every 30 seconds").
// A clock of UNPAUSED seconds from THE FLOOD (the siren; before it nothing in
// the hall threatens anyone, so the calm is not counted). At AFTER_SECS the
// first Doppelghast comes up on the hall riser farthest from the party, then
// one every EVERY_SECS while any living player is still inside the hall,
// never more than MAX alive. The seal ends the clock; a hunter that followed
// the party out keeps hunting, one left inside is deleted with the rest.
// THE RAMP (user 2026-09-25: "there's a timer in the crown where we attempt to
// kick you out or you will die ... if you've been in there longer than ninety
// seconds we start to ramp it up ... Doppelgast and Manglers ... eventually you
// can't stay in there long enough, you will die, so it continues to ramp and
// ramp"). The clock is unpaused seconds from THE ALARM. From AFTER_SECS an
// elite comes up on the hall riser farthest from the party, alternating
// Doppelghast / Mangler; each gap is the last x DECAY down to MIN_SECS, the
// live cap grows by one every CAP_EVERY spawns up to CAP_MAX, and each
// Doppelghast carries one more zombie's worth of health than the last. With
// these numbers: spawns at 90, 120, 144, 163, 178, ... every 5 s from ~4 min,
// cap 2 -> 10. It counts only while a living player is in the hall; the seal
// (everyone out) ends it. This ramp OVERRIDES level.tod_only_zombies (the user
// asked for these two by name) and the shared elite roof; the one ceiling it
// keeps is ACTOR_RESERVE free actor slots, so it can never starve the horde.
#define TOD_FALL_HUNT_AFTER_SECS   90
#define TOD_FALL_HUNT_EVERY_SECS   30     // the first gap
#define TOD_FALL_HUNT_DECAY        0.8    // each gap = the last x this
#define TOD_FALL_HUNT_MIN_SECS     5      // the floor the gap shrinks to
#define TOD_FALL_HUNT_CAP_START    2      // elites alive at once, to begin
#define TOD_FALL_HUNT_CAP_EVERY    2      // +1 to the cap every N spawns
#define TOD_FALL_HUNT_MAX          10     // the cap's ceiling
#define TOD_FALL_HUNT_HP_ZOMBIES   5      // the first Doppelghast (the round director's figure) ...
#define TOD_FALL_HUNT_HP_STEP      1      // ... + this per Doppelghast after it
#define TOD_FALL_HUNT_HP_MAX       16
#define TOD_FALL_HUNT_ACTOR_RESERVE 3

#define TOD_FALL_ENABLED     1
#define TOD_FALL_FLAG        "tod_fall"        // the generated door flag (gen_tower_map.js DOORS, dest "the Causeway")
#define TOD_FALL_ZONE        "crown_zone"      // the hall's zone (gen_tower_map.js ZONES; the START zone)
#define TOD_FALL_SEAL_GRACE  2.0               // seconds the hall must stay empty before the gate re-seals
#define TOD_FALL_SEAL_POLL   0.25
#define TOD_FALL_HULL        24                // player hull margin round the slab box for the crush check
#define TOD_FALL_SEAL_SOUND  "zmb_heavy_door_open"   // the heavy-door cue. NOT in any stock bank this usermap loads (the 17:33 run's probe: ms=-1); the map defines it since 2026-10-05 (sound/aliases/tod_ui.csv, DistMax 2000/2400)
#define TOD_FALL_SEAL_CUE_NEAR 1500           // a player this close to the gate hears the cue AT the gate (LT-fix 2026-10-05) ...
#define TOD_FALL_SEAL_CUE_STEP 400            // ... a farther one hears it this far from him, toward the crown (inside the alias's 2000 reach)
#define TOD_FALL_LOG         1                 // TEMPORARY — logs with dev OFF for the first playtests; zero before publish
#define TOD_LIGHTSTATE_LOG   1                 // TEMPORARY — docs/162 T1's log, same rule


#namespace tod_fall;

function init()
{
	level endon( "end_game" );
	if ( !TOD_FALL_ENABLED )
		return;

	// Set BEFORE the blackscreen: the speed callback runs on the first spawn
	// of round 1 and must already see the crown phase.
	level.tod_fall_phase = true;
	level.tod_fall_gate_flag = TOD_FALL_FLAG;   // _tod_doors::dev_open_all_doors never opens this gate (the run's first buy)
	level.tod_fall_sealed = false;
	level.tod_fall_flood = false;

	// THE FLOOD HOLD — before anything can spawn (the draft's world pause
	// starts 0.5 s after the blackscreen; this runs before the blackscreen).
	flood_hold();

	// docs/162 T1: every spawn re-applies the player's lighting state.
	callback::on_spawned( &on_player_spawned );

	level flag::wait_till( "initial_blackscreen_passed" );
	lightstate_log( "blackscreen" );
	// power_on() runs from flood() now — the lever is the power (see the defines)
	tod_crown_alarm::init();
	lever_spawn();

	// THE ENCLOSED HALLWAY (2026-09-25): the middle door waits for the power,
	// the right room's functional teleporter is owned by _tod_teleport.
	level thread hallway_setup();

	// _tod_doors::init makes every slab Solid + DisconnectPaths and registers
	// it by flag one second after the blackscreen. Bounded wait, then read.
	for ( i = 0; i < 40 && !IS_TRUE( level.tod_doors_ready ); i++ )
		wait 0.25;
	d = undefined;
	if ( isdefined( level.tod_doors_by_flag ) )
		d = level.tod_doors_by_flag[ TOD_FALL_FLAG ];
	if ( !isdefined( d ) || !isdefined( d.tod_slab ) )
	{
		// generator drift — an unsealable crown is survivable, a script error is not
		fall_log( "INIT no door registered for flag " + TOD_FALL_FLAG + " — the crown will never seal" );
		level thread calm_watch();   // the flood must still come, sealed or not
		return;
	}
	level.tod_fall_slab = d.tod_slab;
	fall_log( "INIT gate registered flag=" + TOD_FALL_FLAG + " zone=" + TOD_FALL_ZONE + " players=" + GetPlayers().size );
	if ( TOD_FALL_GATE_OPEN )
	{
		tod_doors::force_open_by_flag( TOD_FALL_FLAG );
		fall_log( "GATE opened free at init (TOD_FALL_GATE_OPEN): the balcony and the overlook are part of the spawn area; the seal still closes it" );
	}
	level thread gate_state_log();
	level thread calm_watch();
	level thread fall_watch();
	level thread hunters_watch();
}

// ---------------------------------------------------------------------------
// THE CALM AND THE FLOOD
// ---------------------------------------------------------------------------

// Clear stock's spawner gate. Stock inits it TRUE in _zm::init, which ran
// inside zm_usermap::main before this module was threaded; bounded wait in
// case that order ever changes, never an init of our own (a second init would
// stamp the flag false under stock's feet).
function flood_hold()
{
	for ( i = 0; i < 100 && !( level flag::exists( TOD_FALL_SPAWN_FLAG ) ); i++ )
		wait 0.05;
	if ( !( level flag::exists( TOD_FALL_SPAWN_FLAG ) ) )
	{
		fall_log( "HOLD failed — flag " + TOD_FALL_SPAWN_FLAG + " never appeared; the flood is not held" );
		return;
	}
	level flag::clear( TOD_FALL_SPAWN_FLAG );
	level.tod_fall_held = true;
	fall_log( "HOLD spawns held on flag " + TOD_FALL_SPAWN_FLAG + " until the alarm" );
}

// Set it again. Idempotent; the seal calls it too, so a gate bought and
// sealed inside the calm (dev money) can never leave the match spawnless.
function release_spawns()
{
	if ( !IS_TRUE( level.tod_fall_held ) )
		return;
	level.tod_fall_held = false;
	if ( level flag::exists( TOD_FALL_SPAWN_FLAG ) )
		level flag::set( TOD_FALL_SPAWN_FLAG );
}

// CALM_SECS of unpaused time after the draft AND the round-1 deal (both hold
// level.tod_upgrade_pause, the same field the hunters' clock skips on).
function calm_watch()
{
	level endon( "end_game" );
	while ( !IS_TRUE( level.tod_class_select_done ) )
		wait 0.1;
	if ( TOD_FALL_LEVER )
	{
		fall_log( "CALM the draft is done; the hall waits for THE LEVER (no timer)" );
		while ( !IS_TRUE( level.tod_fall_lever_pulled ) && !IS_TRUE( level.tod_fall_flood ) )
		{
			wait 0.25;
			if ( IS_TRUE( level.tod_fall_sealed ) )
				return;   // sealed before the pull (dev): the seal released the spawns, no alarm
		}
		return;   // the lever's own thread runs flood()
	}
	fall_log( "CALM the draft is done; " + TOD_FALL_CALM_SECS + " s of unpaused quiet after the deal, then the alarm" );
	ms = 0;
	while ( ms < TOD_FALL_CALM_SECS * 1000 )
	{
		wait 0.25;
		if ( IS_TRUE( level.tod_fall_sealed ) )
			return;   // sealed inside the calm (dev): the seal released the spawns, no alarm
		if ( IS_TRUE( level.tod_upgrade_pause ) )
			continue;   // a frozen world does not count
		ms += 250;
	}
	flood( 0 );
}

// lead_secs: the alarm and the siren come up NOW; the spawns release lead_secs
// later (0 = together, the timed calm's shape). The Doppelghast clock and the
// flood notify count from now either way.
function flood( lead_secs )
{
	if ( IS_TRUE( level.tod_fall_flood ) )
		return;
	level.tod_fall_flood = true;
	level.tod_fall_flood_ms = GetTime();
	// the POWER is its own switch now (the overlook; power_switch_on) — the
	// alarm starts the game, it does not turn the grid on. It DOES light the
	// hall (user 2026-09-25: "the crown lights turn on ... so you can actually
	// see while you're fighting"): script state 2 = Radiant State 3, the dark
	// map with only the hall's lights (gen_tower_map.js HALL_ALARM_LIGHTS).
	if ( !isdefined( level.tod_fall_power_ms ) )
	{
		level util::set_lighting_state( 2 );
		lightstate_log( "alarm_lit" );
	}
	// THE CROWN'S PaP WAKES WITH THE ALARM (user 2026-09-25) — zm_cwpap
	// machine_powered() reads this for the crown machine only.
	level.tod_crown_pap_live = true;
	fall_log( "PAP crown machine live at the alarm (every other machine waits for the power)" );
	level thread alarm_start();
	level notify( "tod_fall_flood" );
	fall_log( "FLOOD round=" + level.round_number + " players=" + GetPlayers().size + " — the alarm is up, the siren is on; spawns in " + lead_secs + " s" );
	level thread flood_release( lead_secs );
}

function flood_release( lead_secs )
{
	level endon( "end_game" );
	if ( isdefined( lead_secs ) && lead_secs > 0 )
	{
		for ( t = 0; t < lead_secs * 4; t++ )
		{
			wait 0.25;
			if ( IS_TRUE( level.tod_fall_sealed ) )
				return;   // the seal released them itself
		}
	}
	release_spawns();
	fall_log( "RELEASE spawns released round=" + level.round_number );
}

// ---------------------------------------------------------------------------
// THE LEVER
// ---------------------------------------------------------------------------

// A point of the prefab's local frame (x forward, y left, z up at yaw 0 —
// the prefab's front is its -y side) placed at org/yaw.
function lever_pt( org, yaw, local )
{
	fwd = AnglesToForward( ( 0, yaw, 0 ) );
	right = AnglesToRight( ( 0, yaw, 0 ) );
	return org + VectorScale( fwd, local[ 0 ] ) - VectorScale( right, local[ 1 ] ) + ( 0, 0, local[ 2 ] );
}

function lever_spawn()
{
	if ( !TOD_FALL_LEVER )
		return;
	// THE ALARM BUTTON: the red button on its stand, the centre of the crown hall (2026-09-28; was a switch on the sanctuary step)
	t = button_spawn( tod_crown_data::alarm_button_org(), tod_crown_data::alarm_button_yaw() );
	if ( isdefined( t ) )
		t thread switch_use_loop( "alarm" );
	else
		level thread lever_fallback();   // calm_watch exits on the flood it raises
	// THE POWER SWITCH: the overlook's rail, armed once the alarm has sounded
	t = switch_spawn( tod_crown_data::power_terminal_org(), tod_crown_data::power_terminal_yaw(), "power" );   // docs/208: the Grid Terminal on the power room's east wall
	if ( isdefined( t ) )
		t thread switch_use_loop( "power" );
	else
		level thread power_fallback();
	level thread power_seal_safety();
}

// One stock power switch (body + handle + use trigger, the prefab's own
// offsets: map_source/_prefabs/zm/zm_core/power_switch.map) at org/yaw.
// Returns the hidden trigger carrying .tod_handle / .tod_fx_org, or undefined
// when the entity pool is full.
function switch_spawn( org, yaw, kind )
{
	// docs/208: THE GRID TERMINAL where the stock lever stood - the panel, its dial and its screen
	// (_tod_power_terminal). The dial is the press's sound + spark anchor (undefined if the pool is full).
	handle = tod_power_terminal::spawn_at( org, yaw );

	t = spawn( "trigger_radius_use", tod_crown_data::power_terminal_trig(), 0, TOD_FALL_LEVER_TRIG_R, TOD_FALL_LEVER_TRIG_H );   // GENERATED: in front of the panel, inside the room, outside its clip
	if ( !isdefined( t ) )
	{
		fall_log( "SWITCH " + kind + " trigger spawn FAILED (entity pool?) — its fallback runs instead" );
		return undefined;
	}
	t TriggerIgnoreTeam();
	t SetCursorHint( "HINT_NOICON" );
	if ( kind == "alarm" )
		t SetHintString( TOD_FALL_ALARM_HINT );
	else
		t SetHintString( TOD_FALL_LEVER_HINT );
	t SetInvisibleToAll();   // shown once armed
	t.tod_handle = handle;
	t.tod_fx_org = org + ( 0, 0, 28 );
	if ( isdefined( handle ) )
		t.tod_fx_org = handle.origin;   // the HOLD button's dial: POWER RESTORED sparks there
	fall_log( "SWITCH " + kind + " spawned at " + org + " yaw=" + yaw + " trig=" + t.origin + " (hidden until armed)" );
	return t;
}

// THE ALARM BUTTON: stand + glowing cap + a use trigger over it. Returns the hidden trigger
// carrying .tod_handle (the cap) / .tod_fx_org, or undefined when the entity pool is full.
function button_spawn( org, yaw )
{
	stand = spawn( "script_model", org );
	if ( isdefined( stand ) )
	{
		stand.angles = ( 0, yaw, 0 );
		stand SetModel( TOD_FALL_BUTTON_STAND );
	}
	cap = spawn( "script_model", org + ( 0, 0, TOD_FALL_BUTTON_CAP_Z ) );
	if ( isdefined( cap ) )
	{
		cap.angles = ( 0, yaw, 0 );
		cap SetModel( TOD_FALL_BUTTON_CAP_ON );
		cap NotSolid();
	}
	t = spawn( "trigger_radius_use", org + ( 0, 0, TOD_FALL_BUTTON_TRIG_LIFT ), 0, TOD_FALL_BUTTON_TRIG_R, TOD_FALL_BUTTON_TRIG_H );
	if ( !isdefined( t ) )
	{
		fall_log( "BUTTON trigger spawn FAILED (entity pool?) — the timed fallback runs instead" );
		return undefined;
	}
	t TriggerIgnoreTeam();
	t SetCursorHint( "HINT_NOICON" );
	t SetHintString( TOD_FALL_ALARM_HINT );
	t SetInvisibleToAll();   // shown once armed
	t.tod_handle = cap;
	t.tod_fx_org = org + ( 0, 0, TOD_FALL_BUTTON_CAP_Z + 4 );
	fall_log( "BUTTON alarm spawned at " + org + " yaw=" + yaw + " stand=" + isdefined( stand ) + " cap=" + isdefined( cap ) + " trig=" + t.origin + " (hidden until armed)" );
	return t;
}

// The press: the cap sinks, goes dark, sparks, the power-on thunk.
function button_press( cap, fx_org )
{
	if ( !isdefined( cap ) )
		return;
	cap MoveZ( 0 - TOD_FALL_BUTTON_PRESS, 0.08 );
	cap PlaySound( TOD_FALL_LEVER_FLIP_SND );
	wait 0.1;
	cap SetModel( TOD_FALL_BUTTON_CAP_OFF );
	spark_burst( fx_org );
	cap PlaySound( TOD_FALL_LEVER_ON_SND );
	fall_log( "BUTTON pressed — cap down " + TOD_FALL_BUTTON_PRESS + ", dark" );
}

// The alarm's pool-full case only: run the old timed calm so a match never stalls.
function lever_fallback()
{
	level endon( "end_game" );
	while ( !IS_TRUE( level.tod_class_select_done ) )
		wait 0.1;
	wait TOD_FALL_CALM_SECS;
	if ( !IS_TRUE( level.tod_fall_sealed ) )
		flood( 0 );
}

// The power's pool-full case only: the grid comes on with the alarm.
function power_fallback()
{
	level endon( "end_game" );
	while ( !IS_TRUE( level.tod_fall_flood ) && !IS_TRUE( level.tod_fall_sealed ) )
		wait 0.25;
	power_switch_on( "the fallback (no power switch)" );
}

// A party that leaves the island without the power (only by dying off it —
// the jump pad itself refuses until the power is on) must not leave the map
// dark for the rest of the match: the seal turns the grid on.
function power_seal_safety()
{
	level endon( "end_game" );
	while ( !isdefined( level.tod_fall_power_ms ) )
	{
		if ( IS_TRUE( level.tod_fall_sealed ) )
		{
			power_switch_on( "the seal (nobody pulled the power switch)" );
			return;
		}
		wait 0.25;
	}
}

function power_is_on()
{
	return ( level flag::exists( "power_on" ) && level flag::get( "power_on" ) );
}

// THE ENCLOSED HALLWAY (user 2026-09-25: "the gate [opens into] an enclosed
// hallway ... left, right, middle ... middle will just be a locked door until
// power is on ... the right will lead to the teleporter"). The left and right
// doors are ordinary _tod_doors buys (tod_crown_power / tod_crown_tele, 1500,
// generated). This owns the two things no door row can:
//   * THE BRIDGE DOOR (map entity tod_crown_bridge_door): Solid + DisconnectPaths
//     at init, opened (Hide + NotSolid + ConnectPaths, the doors' own open) the
//     moment the "power_on" flag rises. Waiting on the FLAG, not on
//     power_switch_on, so every path that powers the map (the switch, the dev
//     harness, stock) opens it.
// The right-hand teleporter is owned by _tod_teleport and links the base.
// Dev logs: [TOD_FALL] HALLWAY ...
function hallway_setup()
{
	level endon( "end_game" );

	door = GetEnt( "tod_crown_bridge_door", "targetname" );
	if ( isdefined( door ) )
	{
		door Solid();
		door DisconnectPaths();
	}
	fall_log( "HALLWAY bridge door " + ( isdefined( door ) ? "shut until power" : "MISSING (no tod_crown_bridge_door in the map)" ) );

	// _tod_teleport owns the functional crown/base pad and its powered states.

	level flag::wait_till( "power_on" );
	if ( isdefined( door ) )
	{
		door NotSolid();
		door ConnectPaths();
		door Hide();
	}
	fall_log( "HALLWAY bridge door OPEN at power round=" + level.round_number );
}

// THE GRID: stock power-on, the veil's clock (_tod_atmosphere::tower_fog reads
// level.tod_fall_power_ms), the lighting-state log. Idempotent.
function power_switch_on( who )
{
	if ( isdefined( level.tod_fall_power_ms ) )
		return;
	level.tod_fall_power_ms = GetTime();
	power_on();
	wait 0.05;    // one frame: the flag's own listeners run first
	lightstate_log( "power_on" );
	level notify( "tod_fall_power" );
	level thread power_wave();
	fall_log( "POWER on by " + who + " round=" + level.round_number + " — perks, PaP, shops, the jump pad; the veil clears" );
}

// THE POWER WAVE (see the defines): one tod_perk_lights glow per floor, top
// down, then the baked lights. The hosts are plain tag_origin script_models on
// the todPerkGlow lane, like the alarm's.
function power_wave()
{
	level endon( "end_game" );
	orgs = tod_crown_data::wave_orgs();
	fx = tod_crown_data::wave_fx();
	hosts = [];
	step = TOD_FALL_WAVE_SECS / orgs.size;
	fall_log( "WAVE start floors=" + orgs.size + " over " + TOD_FALL_WAVE_SECS + " s" );
	// PK23 (2026-10-05): THE WAVE IS HEARD. The surge rushes DOWN the tower with the light (it starts close and recedes,
	// its relays tripping farther and darker), 2D to everyone - the crown phase has no music under it. Its 13.5 s =
	// TOD_FALL_WAVE_SECS + TOD_FALL_WAVE_HOLD_SECS (LOCKSTEP tools/sfx/w2c_sounds/make_sounds.py tod_power_wave).
	foreach ( listener in GetPlayers() )
		listener PlayLocalSound( "tod_power_wave" );
	for ( i = 0; i < orgs.size; i++ )
	{
		h = Spawn( "script_model", orgs[ i ] );
		if ( isdefined( h ) )
		{
			h SetModel( "tag_origin" );
			hosts[ hosts.size ] = h;
			h thread wave_glow( fx[ i ] );
		}
		// THE HAVENS (docs/202): each safe-zone dome boots as the wave passes its floor
		level notify( "tod_power_wave_z", orgs[ i ][ 2 ] );
		wait step;
	}
	wait TOD_FALL_WAVE_HOLD_SECS;
	level util::set_lighting_state( 0 );   // Radiant State 1 = every baked light (LIGHTS_AT_POWER)
	// PK23: the GRID ONLINE - the whole tower lights on this frame, and everyone hears it land
	foreach ( listener in GetPlayers() )
		listener PlayLocalSound( "tod_power_online" );
	wait 0.05;
	lightstate_log( "wave_lit" );
	fall_log( "WAVE lit — lighting state 0 (Radiant 1), hosts=" + hosts.size );
	wait TOD_FALL_WAVE_FADE_SECS;
	foreach ( h in hosts )
		if ( isdefined( h ) )
			tod_perk_lights::set_glow( h, 0 );
	wait 0.5;
	foreach ( h in hosts )
		if ( isdefined( h ) )
			h Delete();
}

function wave_glow( idx )   // self = a wave host
{
	self endon( "death" );
	wait 0.1;   // a snapshot: the client lane resolves tag_origin on the entity's dobj
	tod_perk_lights::set_glow( self, idx );
}

// THE PRESS on THE GRID TERMINAL (docs/208): stock electric_switch's two sounds round the terminal's
// boot - the dial's two turns and the RESTART GRID lighting (~1.4 s) - then the sparks at the HOLD
// button. Returns when the screen reads POWER RESTORED, so power_switch_on lands on that frame.
function switch_flip( handle, fx_org, who )
{
	if ( isdefined( handle ) )
		handle PlaySound( TOD_FALL_LEVER_FLIP_SND );
	tod_power_terminal::boot( who );
	if ( !isdefined( handle ) )
		return;
	// 2026-09-25: on a carrier - bare server PlayFX does not render on this map
	// (the Mangler paid for that), so the flip's sparks were never seen.
	spark_burst( fx_org );
	handle PlaySound( TOD_FALL_LEVER_ON_SND );
}

// One spark burst on a short-lived tag_origin carrier.
function spark_burst( org )
{
	host = Spawn( "script_model", org );
	if ( !isdefined( host ) ) return;
	host SetModel( "tag_origin" );
	host.angles = ( -60, 0, 0 );   // spray up and out
	PlayFXOnTag( TOD_FALL_LEVER_SPARKS, host, "tag_origin" );
	host thread delete_after( 2.0 );
}

function delete_after( secs )
{
	wait secs;
	if ( isdefined( self ) ) self Delete();
}

// THE ALARM SWITCH CALLS THE PLAYER (user 2026-09-25: "there's not enough light in
// the crown for a player to know what to do ... the switch that turns on the alarm
// [needs] to at least spark and there needs to be some light towards it so players
// can actually gravitate towards it"). While it waits for its pull: a steady orange
// glow + light on it (todPerkGlow index 4, the perk-machine lane) and a spark burst
// with an electric crackle every 1.2-2.8 s. Both end the moment it is pulled.
// TOD_FALL_ATTRACT_GLOW retired 2026-09-28 (user: remove the red light above the alarm button).
function switch_attract( fx_org )   // self = the alarm trigger
{
	self endon( "death" );
	self endon( "tod_switch_pulled" );
	level endon( "end_game" );
	// NO GLOW (user 2026-09-28: "remove the light that's above the new alarm
	// trigger ... keep the model, keep the alarm"). The red button model's own
	// emissive cap and the spark bursts still call the player to it.
	glow = undefined;
	snd = Spawn( "script_origin", fx_org );
	self thread attract_cleanup( glow, snd );
	fall_log( "SWITCH alarm ATTRACT on glow=none sparks=1 at " + fx_org );
	bursts = 0;
	for ( ;; )
	{
		wait RandomFloatRange( 1.2, 2.8 );
		spark_burst( fx_org );
		if ( isdefined( snd ) ) snd PlaySound( "tod_shop_spark_" + ( RandomInt( 3 ) + 1 ) );
		bursts++;
		if ( bursts == 1 ) fall_log( "SWITCH alarm ATTRACT first spark" );
	}
}

function attract_cleanup( glow, snd )   // self = the alarm trigger
{
	self util::waittill_any( "death", "tod_switch_pulled" );
	if ( isdefined( glow ) )
	{
		tod_perk_lights::set_glow( glow, 0 );
		glow thread delete_after( 0.5 );
	}
	if ( isdefined( snd ) ) snd thread delete_after( 2.0 );
	fall_log( "SWITCH alarm ATTRACT off" );
}

function switch_use_loop( kind )   // self = the trigger
{
	self endon( "death" );
	level endon( "end_game" );
	handle = self.tod_handle;
	fx_org = self.tod_fx_org;
	while ( !IS_TRUE( level.tod_class_select_done ) )
		wait 0.1;
	if ( kind == "power" )
	{
		// THE ORDER: the alarm starts the game; the power comes after it
		while ( !IS_TRUE( level.tod_fall_flood ) && !power_is_on() )
			wait 0.25;
	}
	if ( !( kind == "power" && power_is_on() ) )
	{
		self SetVisibleToAll();
		if ( kind == "alarm" ) self thread switch_attract( fx_org );
		fall_log( "SWITCH " + kind + " armed — waiting for a pull" );
		while ( true )
		{
			self waittill( "trigger", player );
			if ( kind == "alarm" && ( IS_TRUE( level.tod_fall_flood ) || IS_TRUE( level.tod_fall_sealed ) ) )
				break;
			if ( kind == "power" && power_is_on() )
				break;
			if ( !isdefined( player ) || !IsPlayer( player ) || !zm_utility::is_player_valid( player ) )
				continue;
			if ( IS_TRUE( level.tod_upgrade_pause ) )
				continue;   // a frozen world: the deal is still up
			self SetInvisibleToAll();
			self notify( "tod_switch_pulled" );   // the attract glow + sparks stop
			if ( kind == "alarm" )
				level.tod_fall_lever_pulled = true;   // cuts the intro before the flip (they never overlap)
			fall_log( "SWITCH " + kind + " pulled by " + player.name + " round=" + level.round_number );
			if ( kind == "alarm" )
				button_press( handle, fx_org );
			else
				switch_flip( handle, fx_org, player );
			if ( kind == "alarm" )
				flood( TOD_FALL_LEVER_LEAD_SECS );
			else
				power_switch_on( player.name );
			break;
		}
	}
	self Delete();
}

// Physical fixtures share this existing alarm edge and siren anchor.
function alarm_start()
{
    level endon( "end_game" );
    if ( IS_TRUE( level.tod_crown_alarm_active ) || IS_TRUE( level.tod_fall_sealed ) )
        return;
    tod_crown_alarm::start();
    if ( IS_TRUE( level.tod_crown_alarm_active ) )
    {
        level thread siren( tod_crown_data::alarm_org() );
        level thread alarm_until_escape();
    }
}

// THE ALARM RUNS UNTIL THE ESCAPE DOOR OPENS (user 2026-09-28: "the sound of the
// alarm and the nuke sound ... should continue playing until that door is open
// ... once they open the door to escape then the alarm system will turn off").
// The escape door is the hall's 5000 gate (flag TOD_FALL_FLAG). Its opening
// turns the whole system off - siren and beacons; the seal still does too.
// 2026-09-29: alarm_stop() raises tod_fall_alarm_off FIRST and this thread ends
// on that notify, so calling it inline killed this thread mid-call: the siren
// and the beacons were never stopped at the door (the 13:03 run: "ALARM off"
// at the door, "SIREN off" only at the seal). It runs on its own thread now,
// the way the seal has always called it.
function alarm_until_escape()
{
    level endon( "end_game" );
    level endon( "tod_fall_alarm_off" );
    while ( !level flag::get( TOD_FALL_FLAG ) && !IS_TRUE( level.tod_fall_sealed ) )
        wait 0.25;
    fall_log( "ALARM off: " + ( ( level flag::get( TOD_FALL_FLAG ) ) ? "the escape door opened" : "the crown sealed" ) );
    level thread alarm_stop();
}

// The siren: the wind-up one-shot, then at TOD_FALL_SIREN_LOOP_AT the LOOPING
// row takes over on the same host as its ENTITY LOOP SOUND (script_origin +
// PlayLoopSound, the stock lane), crossfading over TOD_FALL_SIREN_XFADE. It runs
// until siren_stop: nothing times it out. Every row is Pauseable, so an ESC pause
// pauses the wind-up and this thread's waits together, and the loop resumes with
// the game. A once-a-second guard brings the loop straight back if anything ever
// deletes the host while the alarm is up.
function siren( org )
{
	level endon( "end_game" );
	level endon( "tod_fall_alarm_off" );   // siren_stop owns the host from here
	e = spawn( "script_origin", org );
	level.tod_fall_siren_ent = e;
	level.tod_fall_siren_on = true;
	e PlaySound( TOD_FALL_SIREN_START );
	fall_log( "SIREN on: wind-up " + TOD_FALL_SIREN_START + ", the loop takes over at " + TOD_FALL_SIREN_LOOP_AT + " s and runs until the escape door opens" );
	wait TOD_FALL_SIREN_LOOP_AT;
	if ( !IS_TRUE( level.tod_fall_siren_on ) || !isdefined( e ) )
		return;
	e PlayLoopSound( TOD_FALL_SIREN_LOOP, TOD_FALL_SIREN_XFADE );
	fall_log( "SIREN loop on: " + TOD_FALL_SIREN_LOOP + " (the host's loop sound; only the escape door or the seal stops it)" );
	secs = 0;
	while ( IS_TRUE( level.tod_fall_siren_on ) )
	{
		wait 1;
		if ( !IS_TRUE( level.tod_fall_siren_on ) )
			return;
		secs++;
		if ( !isdefined( level.tod_fall_siren_ent ) )
		{
			e = spawn( "script_origin", org );
			level.tod_fall_siren_ent = e;
			e PlayLoopSound( TOD_FALL_SIREN_LOOP, TOD_FALL_SIREN_XFADE );
			fall_log( "SIREN host lost after " + secs + " s - the loop restarted" );
		}
		if ( secs % 60 == 0 )
			fall_log( "SIREN still looping after " + secs + " s" );
	}
}

// The alarm powers off: the loop fades out under the wind-down, then the host
// goes once the wind-down has played (deleting it at once would cut it off).
// Safe to call twice (the door, then the seal).
function siren_stop()
{
	level.tod_fall_siren_on = false;
	e = level.tod_fall_siren_ent;
	level.tod_fall_siren_ent = undefined;
	if ( !isdefined( e ) )
		return;
	e StopLoopSound( TOD_FALL_SIREN_STOP_FADE );
	e StopSound( TOD_FALL_SIREN_START );   // a gate bought during the wind-up
	e PlaySound( TOD_FALL_SIREN_STOP );
	fall_log( "SIREN off: the loop fades under the wind-down " + TOD_FALL_SIREN_STOP + " (" + TOD_FALL_SIREN_STOP_SECS + " s)" );
	wait( TOD_FALL_SIREN_STOP_SECS + 0.5 );
	if ( isdefined( e ) )
	{
		e StopSounds();
		e Delete();
	}
}

// The whole alarm system off: the beacons go dark and still at once and the
// siren winds down on its own thread. Always call it with `level thread`.
// The seal leaves the physical beacons mounted, dark and stationary.
function alarm_stop()
{
    level notify( "tod_fall_alarm_off" );
    level thread siren_stop();
    tod_crown_alarm::stop();
}

// ---------------------------------------------------------------------------
// THE HUNTERS
// ---------------------------------------------------------------------------

// -> a random living player inside the hall, or undefined.
function player_in_hall()
{
	c = [];
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
			continue;
		if ( isdefined( p.sessionstate ) && p.sessionstate != "playing" )
			continue;
		// A DOWNED PLAYER IS NOT "SOMEONE IN THE HALL" (2026-10-04, the first real-run review; god mode
		// never downed anyone): the ramp is the reason not to STAY, and a downed teammate cannot leave. Left
		// counting, he kept the ramp spawning hunters on him while the party that had jumped waited.
		if ( p laststand::player_is_in_laststand() )
			continue;
		if ( tod_crown_data::in_hall( p.origin ) )
			c[ c.size ] = p;
	}
	if ( c.size == 0 )
		return undefined;
	return c[ RandomInt( c.size ) ];
}

// THE RAMP (see the defines). Starts at THE FLOOD (the alarm pull).
function hunter_live()
{
	return tod_doppelghast::alive_count() + tod_mangler::live_manglers().size;
}

function hunters_watch()
{
	level endon( "end_game" );
	while ( !IS_TRUE( level.tod_fall_flood ) )
	{
		if ( IS_TRUE( level.tod_fall_sealed ) )
			return;   // sealed before the flood (dev): no hunt
		wait 0.25;
	}
	level.tod_fall_clock_ms = 0;
	next_at = TOD_FALL_HUNT_AFTER_SECS * 1000;
	gap = TOD_FALL_HUNT_EVERY_SECS;
	spawned = 0;
	doppels = 0;
	fall_log( "RAMP clock started at the alarm: first elite at " + TOD_FALL_HUNT_AFTER_SECS + " s, gap " + TOD_FALL_HUNT_EVERY_SECS + " s x" + TOD_FALL_HUNT_DECAY + " to " + TOD_FALL_HUNT_MIN_SECS + " s, cap " + TOD_FALL_HUNT_CAP_START + " -> " + TOD_FALL_HUNT_MAX );
	for ( ;; )
	{
		wait 0.25;
		if ( !IS_TRUE( level.tod_fall_phase ) || IS_TRUE( level.tod_fall_sealed ) )
		{
			fall_log( "RAMP over — the crown is sealed at " + ( level.tod_fall_clock_ms / 1000 ) + " s, spawned=" + spawned );
			return;
		}
		if ( IS_TRUE( level.tod_upgrade_pause ) )
			continue;   // a frozen world does not count
		level.tod_fall_clock_ms += 250;
		if ( level.tod_fall_clock_ms < next_at )
			continue;

		target = player_in_hall();
		if ( !isdefined( target ) )
		{
			next_at = level.tod_fall_clock_ms + 1000;   // nobody inside: look again in 1 s, the gap does not advance
			continue;
		}
		cap = TOD_FALL_HUNT_CAP_START + int( spawned / TOD_FALL_HUNT_CAP_EVERY );
		if ( cap > TOD_FALL_HUNT_MAX )
			cap = TOD_FALL_HUNT_MAX;
		n = hunter_live();
		if ( n >= cap || GetFreeActorCount() < TOD_FALL_HUNT_ACTOR_RESERVE )
		{
			fall_log( "RAMP held at " + ( level.tod_fall_clock_ms / 1000 ) + " s — alive=" + n + " cap=" + cap + " free_actors=" + GetFreeActorCount() );
			next_at = level.tod_fall_clock_ms + 1000;
			continue;
		}
		org = tod_doppelghast::hall_spot();
		kind = ( ( spawned % 2 ) == 0 ? "doppelghast" : "mangler" );
		if ( kind == "mangler" )
		{
			facing = VectorToAngles( target.origin - org );
			actor = tod_mangler::spawn_at( org, target, ( 0, facing[ 1 ], 0 ) );
		}
		else
		{
			hp = TOD_FALL_HUNT_HP_ZOMBIES + doppels * TOD_FALL_HUNT_HP_STEP;
			if ( hp > TOD_FALL_HUNT_HP_MAX )
				hp = TOD_FALL_HUNT_HP_MAX;
			actor = tod_doppelghast::spawn_hunter( org, target, hp );
		}
		if ( !isdefined( actor ) )
		{
			fall_log( "RAMP denied at " + ( level.tod_fall_clock_ms / 1000 ) + " s kind=" + kind + " (SpawnActor) — retry in 2 s" );
			next_at = level.tod_fall_clock_ms + 2000;
			continue;
		}
		spawned++;
		if ( kind == "doppelghast" )
			doppels++;
		fall_log( "RAMP spawn #" + spawned + " " + kind + " at " + ( level.tod_fall_clock_ms / 1000 ) + " s gap=" + gap + " alive=" + hunter_live() + " cap=" + cap + " hp=" + actor.health + " round=" + level.round_number );
		next_at = level.tod_fall_clock_ms + int( gap * 1000 );
		gap = gap * TOD_FALL_HUNT_DECAY;
		if ( gap < TOD_FALL_HUNT_MIN_SECS )
			gap = TOD_FALL_HUNT_MIN_SECS;
	}
}

// ---------------------------------------------------------------------------
// THE POWER
// ---------------------------------------------------------------------------

// THE GRID COMES ON AT THE LEVER (2026-09-25; it was live from the first frame
// from docs/160 until then). Idempotent.
function power_on()
{
	if ( level flag::exists( "power_on" ) && level flag::get( "power_on" ) )
		return;
	// The dev harness's pair, in the harness's order (the retired dev_spire_harness):
	// "never poke power_on by hand — it leaves the perk machines paused".
	zm_power::turn_power_on_and_open_doors();
	zm_perks::perk_unpause_all_perks();
	fall_log( "POWER on (the lever; the plaza switch is vestigial under DESCENT)" );
}

// ---------------------------------------------------------------------------
// THE SEAL
// ---------------------------------------------------------------------------

// THE SEALED AREA. docs/163 (a peer session, 2026-09-24) cuts the causeway
// to two stubs with a one-way JUMP PAD between them: the hall plus its stub
// become an ISLAND, and "everyone is out" then means everyone has CROSSED —
// a player still on the crown's stub could not walk back in, but could not
// leave either, and the seal must not strand them. GENERATED crown data
// carries both predicates: jumppad_enabled() (1 while the road is cut) and
// on_crown_island() (the hall + its stub; in_hall() when the road is whole).
// One reader here, so the seal and the sweep can never disagree.
function in_sealed_area( org )
{
	if ( tod_crown_data::jumppad_enabled() )
		return tod_crown_data::on_crown_island( org );
	return tod_crown_data::in_hall( org );
}

// -> -1 when no living player exists (a wipe: nothing to seal for), else how
// many living players are still inside the sealed area (the doorway included;
// the crown's stub too while the road is cut). Last stand counts as living —
// a crawler in the hall has not left it.
function living_in_hall()
{
	players = GetPlayers();
	n_live = 0;
	n_in = 0;
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
			continue;
		if ( isdefined( p.sessionstate ) && p.sessionstate != "playing" )
			continue;   // a spectator's origin rides a teammate's camera
		n_live++;
		// docs/163: a player MID-FLIGHT on the jump pad (~4.5 s over the void,
		// outside every zone volume) has not crossed yet — counting them as
		// out would seal the gate while nobody occupies any zone, and stock's
		// empty-spawner failsafe (hall_spawn_guard, below) would then re-arm
		// the hall. The flag is _tod_jumppad's (the peer session's module).
		if ( in_sealed_area( p.origin ) || IS_TRUE( p.tod_jumppad_flying ) )
			n_in++;
	}
	if ( n_live == 0 )
		return -1;
	return n_in;
}

// docs/163 (the jump-pad session's finding): stock's manage_zones failsafe —
// "Special logic for empty spawner list", _zm_zonemgr.gsc ~line 950 — sets
// the INITIAL zone back to is_active / is_occupied / is_spawning_allowed =
// TRUE whenever no enabled zone is occupied (every living player mid-flight
// over the void, or a co-op moment with everyone outside every volume). The
// write is sticky and the initial zone is crown_zone, so the sealed hall
// would spawn zombies behind its gate. Re-assert every 0.5 s for the rest of
// the closed period; stop when the bottom transit return restores the crown.
function hall_spawn_guard()
{
	level endon( "end_game" );
	fixed = 0;
	for ( ;; )
	{
		wait 0.5;
		if ( IS_TRUE( level.tod_fall_return_open ) ) return;
		if ( !isdefined( level.zones ) || !isdefined( level.zones[ TOD_FALL_ZONE ] ) )
			continue;
		z = level.zones[ TOD_FALL_ZONE ];
		if ( !IS_TRUE( z.is_spawning_allowed ) )
			continue;
		z.is_spawning_allowed = false;
		fixed++;
		if ( fixed == 1 )
			fall_log( "GUARD the hall zone's spawning came back on after the seal (stock's empty-spawner failsafe) — cleared, and will keep clearing" );
	}
}

// True while a living player's origin is inside the slab's box (+ hull): a
// brush that solidifies on top of a player is the crush case every door slab
// in this map has been careful about.
function slab_occupied()
{
	mn = tod_crown_data::fall_gate_mins();
	mx = tod_crown_data::fall_gate_maxs();
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
			continue;
		o = p.origin;
		if ( o[ 0 ] < mn[ 0 ] - TOD_FALL_HULL || o[ 0 ] > mx[ 0 ] + TOD_FALL_HULL )
			continue;
		if ( o[ 1 ] < mn[ 1 ] - TOD_FALL_HULL || o[ 1 ] > mx[ 1 ] + TOD_FALL_HULL )
			continue;
		if ( o[ 2 ] < mn[ 2 ] - 8 || o[ 2 ] > mx[ 2 ] )
			continue;
		return true;
	}
	return false;
}

// One line, 6 s after the gate registers (after _tod_doors and any dev door
// harness have run): is the Fall's gate still SHUT? The user's rule is that it
// is, until someone buys it.
function gate_state_log()
{
	level endon( "end_game" );
	wait 6;
	flag_set = level flag::get( TOD_FALL_FLAG );
	fall_log( "GATE state at +6 s: " + ( flag_set ? "OPEN (flag set)" : "SHUT (a 5000 buy)" ) + " gate_open_define=" + TOD_FALL_GATE_OPEN + " dev=" + IS_TRUE( level.tod_dev ) );
}

function fall_watch()
{
	level endon( "end_game" );

	level flag::wait_till( TOD_FALL_FLAG );
	level.tod_fall_open_ms = GetTime();
	fall_log( "OPEN round=" + level.round_number + " players=" + GetPlayers().size + " flood=" + IS_TRUE( level.tod_fall_flood ) + " — waiting for the hall to empty" );

	empty_since = undefined;
	for ( ;; )
	{
		wait TOD_FALL_SEAL_POLL;
		if ( IS_TRUE( level.tod_fall_return_open ) ) return;

		n_in = living_in_hall();
		if ( n_in < 0 )
		{
			empty_since = undefined;   // nobody alive — a wipe is not an exit
			continue;
		}
		if ( n_in > 0 )
		{
			if ( isdefined( empty_since ) )
				fall_log( "EMPTY aborted — " + n_in + " living player(s) back inside the hall" );
			empty_since = undefined;
			continue;
		}
		if ( !isdefined( empty_since ) )
		{
			empty_since = GetTime();
			fall_log( "EMPTY every living player is out of the hall; sealing in " + TOD_FALL_SEAL_GRACE + " s" );
			continue;
		}
		if ( GetTime() - empty_since < TOD_FALL_SEAL_GRACE * 1000 )
			continue;
		if ( slab_occupied() )
			continue;   // someone is standing in the doorway box: wait, never crush

		seal();
		return;
	}
}

// Reaching the bottom earns the crown return. Keep the opening phase finished,
// but restore the real gate, zombie pressure and co-op respawns before landing.
function open_for_transit_return()
{
	if ( IS_TRUE( level.tod_fall_return_open ) ) return true;
	if ( !isdefined( level.tod_fall_slab ) || !isdefined( level.zones )
	  || !isdefined( level.zones[ TOD_FALL_ZONE ] ) ) return false;
	level.tod_fall_return_open = true;
	level.tod_fall_phase = false;
	// sealed records completion of the opening sequence; return_open is its exit.
	level.tod_fall_sealed = true;
	release_spawns();
	level thread alarm_stop();
	level.tod_fall_slab NotSolid();
	level.tod_fall_slab ConnectPaths();
	level.tod_fall_slab Hide();
	level.zones[ TOD_FALL_ZONE ].is_spawning_allowed = true;
	pts = struct::get_array( "player_respawn_point", "targetname" );
	n = 0;
	for ( i = 0; i < pts.size; i++ )
	{
		if ( !isdefined( pts[ i ] ) || !isdefined( pts[ i ].script_noteworthy ) ) continue;
		if ( pts[ i ].script_noteworthy != TOD_FALL_ZONE ) continue;
		pts[ i ].locked = false;
		n++;
	}
	level notify( "tod_fall_return_open" );
	fall_log( "RETURN_OPEN crown gate open, spawning restored, respawns=" + n );
	return true;
}

function seal()
{
	slab = level.tod_fall_slab;
	if ( isdefined( slab ) )
	{
		slab Show();
		slab Solid();
		slab DisconnectPaths();   // MANDATORY: the navmesh ignores entity collision entirely
	}
	level.tod_fall_phase = false;   // sprint override + crown trickle off (readers field-poll)
	level.tod_fall_sealed = true;
	level.tod_fall_seal_ms = GetTime();
	release_spawns();               // a seal inside the calm must not leave the match spawnless
	level thread alarm_stop();      // beacon + siren down (waits a snapshot; never delays the seal)

	// The hall stops spawning. is_spawning_allowed is what stock's spawner
	// reads per zone (_zm_zonemgr::manage_zones); is_enabled is deliberately
	// left alone — it is sticky in stock and only the playable-area monitor
	// reads it, and nobody is inside to be monitored.
	if ( isdefined( level.zones ) && isdefined( level.zones[ TOD_FALL_ZONE ] ) )
		level.zones[ TOD_FALL_ZONE ].is_spawning_allowed = false;
	level thread hall_spawn_guard();   // docs/163: the failsafe re-arms it; keep it off

	n_locked = lock_hall_respawns();
	n_deleted = clear_hall();

	org = tod_crown_data::gate_org();
	tod_perk_scatter::derez_burst( org );
	seal_cue( org );
	IPrintLnBold( "THE CROWN SEALS BEHIND YOU" );

	level notify( "tod_fall_sealed" );
	fall_log( "SEAL round=" + level.round_number + " open_for_ms=" + ( GetTime() - level.tod_fall_open_ms )
	          + " respawns_locked=" + n_locked + " zombies_deleted=" + n_deleted );
}

// THE SEAL IS HEARD (LT-fix 2026-10-05; the user's 17:33 run). The cue played only AT the gate, and the seal fires
// 2 s after the last living player has left the hall: in that run he had just landed from the first jump, ~6,920 u
// from the gate, far past the alias's 2000 u reach, so "THE CROWN SEALS BEHIND YOU" printed in silence (and the
// alias itself was not loaded until the map defined it, 2026-10-05). Now a player within TOD_FALL_SEAL_CUE_NEAR of
// the gate hears it there, and every other living player hears it TOD_FALL_SEAL_CUE_STEP from him toward the crown,
// played to him alone (PlaySoundToPlayer on a temp script_origin, cleaned up like play_sound_at_origin's): the slam
// comes from behind him, where the crown is. SEAL_CUE logs each lane and the alias length (ms <= 0 = not loaded).
function seal_cue( org )
{
	tod_perk_scatter::play_sound_at_origin( org, TOD_FALL_SEAL_SOUND, 4 );   // at the gate, for anyone in its earshot
	near = 0;
	far = 0;
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || !isalive( p ) )
			continue;
		d = Distance( p.origin, org );
		if ( d <= TOD_FALL_SEAL_CUE_NEAR )
		{
			near++;
			continue;
		}
		dir = VectorNormalize( ( org[ 0 ] - p.origin[ 0 ], org[ 1 ] - p.origin[ 1 ], 0 ) );
		at = p.origin + dir * TOD_FALL_SEAL_CUE_STEP + ( 0, 0, 48 );
		e = Spawn( "script_origin", at );
		if ( !isdefined( e ) )
			continue;   // entity pool full: drop the sound, never throw
		e PlaySoundToPlayer( TOD_FALL_SEAL_SOUND, p );
		e thread tod_perk_scatter::emitter_cleanup( 4 );
		far++;
		fall_log( "SEAL_CUE player=" + p GetEntityNumber() + " gate_dist=" + int( d ) + " at=" + at );
	}
	fall_log( "SEAL_CUE alias=" + TOD_FALL_SEAL_SOUND + " ms=" + SoundGetPlaybackTime( TOD_FALL_SEAL_SOUND ) + " near_gate=" + near + " far=" + far );
}

// Lock the hall's own respawn group (script_noteworthy == the hall zone) so
// no co-op respawn can ever land behind the shut gate. Stock unlocked it when
// the zone enabled (enable_zone) and reads .locked at every selection site.
function lock_hall_respawns()
{
	n = 0;
	pts = struct::get_array( "player_respawn_point", "targetname" );
	for ( i = 0; i < pts.size; i++ )
	{
		if ( !isdefined( pts[ i ] ) || !isdefined( pts[ i ].script_noteworthy ) )
			continue;
		if ( pts[ i ].script_noteworthy != TOD_FALL_ZONE )
			continue;
		pts[ i ].locked = true;
		n++;
	}
	return n;
}

// Delete every ORDINARY zombie left inside the sealed hall (see the header).
// Never an elite: they carry contracts (music refcounts, the boss director's
// slots) and tod_boss_stuck_watch relocates a stalled one with an entrance.
// zombie_total is untouched (it counts UNSPAWNED zombies), so THE TWIST's
// round contract is untouched too.
function clear_hall()
{
	n = 0;
	team = ( isdefined( level.zombie_team ) ? level.zombie_team : "axis" );
	ai = GetAITeamArray( team );
	for ( i = 0; i < ai.size; i++ )
	{
		z = ai[ i ];
		if ( !isdefined( z ) || !isalive( z ) )
			continue;
		if ( !in_sealed_area( z.origin ) )
			continue;   // the hall, or the whole island while the road is cut (a body on the stub is as stranded as one in the hall)
		// a Doppelghast still inside is boss-flagged but self-driven (no
		// relocation entrance of its own): it goes with the hall too
		if ( IS_TRUE( z.tod_doppelghast ) || IS_TRUE( z.tod_mangler ) )
		{
			z Delete();
			n++;
			continue;
		}
		if ( IS_TRUE( z.is_boss ) || IS_TRUE( z.acc_is_boss ) || IS_TRUE( z.acc_is_mini_boss ) )
			continue;
		if ( !( z zombie_utility::is_zombie() ) )
			continue;
		z Delete();
		n++;
	}
	return n;
}

// ---------------------------------------------------------------------------
// DIAGNOSTICS
// ---------------------------------------------------------------------------

// docs/162 T1 — the lighting-state log (10 §7.1's sketch, built). The level's
// script state (util::set_lighting_state writes level.lighting_state; stock
// zm_usermap::main sets 1) and each player's own GetLightingState(). Expected
// today: level=1 player=1 at every line. Read with the two test lights.
function lightstate_log( at )
{
	if ( !TOD_LIGHTSTATE_LOG && !IS_TRUE( level.tod_dev ) )
		return;
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
		lightstate_log_player( players[ i ], at );
}

function lightstate_log_player( p, at )
{
	if ( !TOD_LIGHTSTATE_LOG && !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	if ( !isdefined( p ) || !isplayer( p ) )
		return;
	lvl = ( isdefined( level.lighting_state ) ? level.lighting_state : -1 );
	line = "[TOD_LIGHTSTATE] ms=" + GetTime() + " at=" + at + " ent=" + p GetEntityNumber()
	       + " level=" + lvl + " player=" + p GetLightingState();
	/#
	PrintLn( line );
	#/
}

// self = the player, on every spawn (callback::on_spawned).
function on_player_spawned()
{
	self endon( "disconnect" );
	wait 0.05;   // the spawn's own state re-apply lands first
	lightstate_log_player( self, "spawned" );
}

// The proven PrintLn pattern (CLAUDE.md dev-diagnostics): assemble outside
// the developer block, print inside it.
function fall_log( msg )
{
	if ( !TOD_FALL_LOG && !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_FALL] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
