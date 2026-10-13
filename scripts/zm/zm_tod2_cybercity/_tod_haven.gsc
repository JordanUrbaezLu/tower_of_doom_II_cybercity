// =============================================================================
// _tod_haven.gsc — THE HAVENS: the safe zones on floors 10 / 20 / 30 / 40 (docs/202).
//
// User 2026-10-02: "Our safe zones on this map need to act more like a safe zone
// and maybe have like an aura around them ... a dome or like a force field that
// animates when you walk in and walk out. And maybe has a small visual effect on
// your screen ... when zombies go in, they will be ... 33% slower and 33% less
// damage."
//
// User 2026-10-03 (v3, THE GUARDED HAVEN): "the dome should be evil at first have
// doppleghast inside and a couple manglers. You must kill them and then the area
// turns into a safe zone. So you must defeat this boss area to take it. No effects
// or safe visuals and all that until you defeat those elites. So two distinct
// states. One when its not safe and one when it is after defeating them."
//
// User 2026-10-03 (v4, THE WHOLE HALL): "Safe zone should be the entire area. All
// things should be encompassed by it. So the radius should bigger and also the
// elites are not allowed to leave the dome. They are stuck inside so you must go
// inside and kill them. And bullets cannot go in or outside the dome. Until its a
// safe zone. Then bullets can shoot through and kill things both ways. But yes all
// perks and ammo crates pap etc should be inside of the dome. Going inside will
// make your screen dark like you are being taken over by the darkness. Not crazy
// but for sure noticable and sligtly annoying. But of course once its a safe zone
// its fine."
//
// Each breather floor carries a HAVEN (tools/haven_layout.js cuts it). v2, THE
// HEART: the tower's core opens at the haven floor into a hall with a loggia under
// the next lap's flights, the teleporter (the Battle Arena gate on 40) at the
// field's centre. v4: the field is AS WIDE AS THE HALL (a low dome, its sphere's
// centre under the floor) and every machine stands inside it, ringing the pad.
// This module is the field's whole life, in TWO STATES:
//
//  * POWER. The domes are dark until the tower's power returns, then each one
//    BOOTS as _tod_fall's power wave rolls down past its floor (flicker, flash,
//    the ignite sound) - CORRUPTED: a crimson lattice, a dark hum, embers and
//    red arcs crawling it, the floor sign glitching red. A fallback boots any
//    haven the wave never reached. A corrupted field does NOTHING to anyone: no
//    slow, no damage cut, no ripple, no kill tax. Its pad (and the Battle Arena
//    gate on 40) is dead until the haven is taken (level.tod_haven_locked_fn).
//  * THE GUARDIANS. The first time a player comes near the heart (the wake band:
//    the hall, its porch, the galleries over it) the field convulses (the wake
//    effect + roar) and its guardians RISE inside it, each on its own spot round
//    the field: Doppelghasts and Manglers (guard_counts: more the deeper the floor,
//    one more Doppelghast for a party of three or four), with their own HP in round
//    zombies. v4: THEY NEVER LEAVE THE FIELD - they hunt only players INSIDE it
//    (tod_hunt_filter, read by _tod_doppelghast / _tod_mangler's hunt_target) and
//    walk back to their spot when nobody is in; one found outside it (a leap, a
//    chase past the rim) is put back on a free spot inside (the FENCE), and their
//    stuck relocation lands inside too (tod_reloc_fn). Every guardian death cracks
//    the dome red (the HUD counts them down); the LAST one CLEANSES the haven.
//  * THE BARRIER (v4, corrupted only). A shell of brushes on the field's sphere
//    (the map's tod_haven_barrier_<floor>, a script_brushmodel in a weapon + missile
//    clip material that bodies walk through) is SOLID from the boot to the cleanse:
//    bullets, arrows and grenades stop on it in both directions (a crimson ripple +
//    a zap where a shot lands: shot_watch), and the damage that has no line to stop
//    - splash, a swing over the rim, scripted hits - is refused across it in both
//    directions: actor_damage_gate (enemies, wrapping level.callbackActorDamage) and
//    level.tod_haven_barrier_fn (players, _tod_bosses' damage lane). A guardian
//    always counts as inside its own field. At the cleanse the barrier goes and
//    "bullets can shoot through and kill things both ways".
//  * THE DARKNESS (v4, corrupted only): inside a corrupted field the screen goes dark
//    (TodHaven.lua: a smoky veil that breathes) and the darkness is heard (the swallow
//    as it takes you, a heartbeat-and-whisper breath re-played while you stay). It
//    lifts the moment you leave or the haven is taken.
//  * THE CORRUPTED LOOK (v5, user 2026-10-04: "I like the two states of the dome to
//    be quite different"). The corrupted dome is its OWN mesh (tools/haven/make_dome.py:
//    a tenth of its cells breached, the rest cracked panes with ragged glowing seams)
//    where the safe one is a clean lattice. It turns in RATCHETS (a broken mechanism,
//    faster while its guardians are up), BROWNS OUT now and then (the dim skin, a dying
//    tube), GROANS from a random point of its rim (3D), its heart throws a throbbing
//    RED LIGHT on the hall; the wake swaps its loop for the FURY (the fight's frenzy)
//    and every guardian death shakes the floor. The safe dome spins smoothly, breathes
//    its heartbeat and holds a steady cyan light.
//  * THE PURIFICATION (v5; was "the cleanse": one stutter and a flash). The last
//    guardian's death starts ONE timeline (purge_run), ~4.5 s:
//      1. THE CONVULSION (TOD_HAVEN_PURGE_CONVULSE_SECS): the heart strobes on an
//         accelerating schedule (purge_strobe_steps(); the dome's own SetModel strobe,
//         the effect's flashes and the sound's clicks all ride it), arcs and lightning
//         snap over the sphere, the floor quakes, the dark hum fades out, the sign
//         stutters; the players inside feel the veil GRIP and flicker with each strobe.
//      2. THE COLLAPSE: the field IMPLODES (beads rushing inward over the whole sphere,
//         a white flash + a real light flash), the dome and the barrier GO, every
//         ordinary zombie inside dies (the stock nuke's idiom), the players inside see
//         black for TOD_HAVEN_PURGE_VOID_SECS.
//      3. THE BLOOM (purify): the field is SAFE from this instant - the bloom effect
//         + chord, FLOOR N HAVEN SECURED to everyone (a bigger flash for those on the
//         floor), TOD_HAVEN_CLEANSE_PTS each, players inside become members of a safe
//         field at once (the kill tax, the bleed-out grace, the tint; the darkness
//         lifts with its own cue), every enemy inside is slowed at once; the safe dome
//         INFLATES from a point (SetScale, eased) as the sign flickers to the district.
//      4. SETTLE: flash -> pulse -> base, the safe hum starts. From here the field is
//         the sanctuary below, for the rest of the match.
//    cleanse() is the entry (the state turns "purge" at once: the field is not safe
//    through the convulsion, its barrier still stands); collapse() and purify() are
//    the two wait-free beats the gate runs.
//  * MEMBERSHIP. Every TOD_HAVEN_TICK every player and every enemy AI is tested
//    against every LIVE field: v4, the SPHERE - the point haven_body_up() over its
//    origin within haven_in_r3() of the sphere's centre (out past haven_out_r3()),
//    inside a z band round the floor - so standing on the ring never flickers and
//    the galleries over the dome stay outside it. A corrupted field's membership
//    drives the HUD (CORRUPTED HAVEN, the darkness), the guardians' targets and the
//    barrier's damage gate.
//  * THE SLOW (33%, safe only). An enemy inside carries self.tod_safe_mult =
//    TOD_HAVEN_SLOW. _tod_zombie_speed multiplies it into the ONE rate line every
//    ordinary zombie gets (apply_speed_for_round), into the elite slow lanes and
//    the pause restore; the Doppelghast and Mangler chase loops read it while
//    they move. The edge re-applies the rate at once. THE SLOW IS VISIBLE (user
//    2026-10-03, tweak #1): a small carrier linked to the slowed enemy plays
//    fx_tod_haven_slowed (cyan arcs round the body, frost sifting off it), at most
//    TOD_HAVEN_SLOW_FX_MAX of them per field at once.
//  * THE DAMAGE CUT (33%, safe only). level.tod_safezone_dr is read by _tod_bosses
//    in BOTH player-damage lanes (the normal fold and the Panzer-melee
//    short-circuit), for enemy damage only (never self, never a fall).
//  * THE KILL PAY (25%, safe only; user 2026-10-02: "Kills inside a zone are at
//    25% money. As well to avoid players from just sitting in zones"). A player
//    standing inside a safe field carries self.tod_haven_pay = TOD_HAVEN_KILL_PAY,
//    and every kill payout that goes to them reads it (kill_pay / kill_preview).
//  * THE BLEED-OUT GRACE (user 2026-10-03, tweak #3; safe only): a player downed
//    inside a safe field bleeds out TOD_HAVEN_BLEEDOUT times slower (stock reads
//    self.n_bleedout_time_multiplier at the down); the HUD's bleed bars read the
//    same mask (tod_haven_bleed) so they drain at the real rate.
//  * THE SPAWN CALM (user 2026-10-03, tweak #2): _tod_endless_rounds' x1.19 rest
//    now asks level.tod_haven_calm_fn - true only while a living player stands
//    INSIDE a safe field (the loggia, where kills pay in full, no longer calms the
//    spawn clock).
//  * THE FLOOR SIGN (user 2026-10-03, tweak #5): a lit card on the hall's S wall
//    reading FLOOR N in the map's typeface: red and glitching while corrupted, the
//    district's colour once safe.
//  * THE FEEDBACK (safe). A player crossing in or out: a ripple on the field where
//    they cross, the dome flashes, the enter / exit sound, their screen's tint
//    (TodHaven.lua, the zero-bit tod_haven event). A zombie forcing its way in:
//    red-orange sparks + a crackle. A hit taken inside: the tint flickers + a tink.
//
// ZERO new clientfields (the clientuimodel pool is at 61/61): the HUD rides
// LuiNotifyEvent; world feedback rides short-lived tag_origin carriers (the
// proven server PlayFXOnTag route: _tod_lucky::fx_at).
//
// Logs `[TOD_HAVEN]` (dev): INIT, BOOT, BARRIER, WAKE, GUARD_SPAWN / GUARD_DENIED /
// GUARD_FENCE / GUARD_RELOC / GUARD_DOWN, PURGE (phase=convulse / collapse / bloom /
// settled, with the collapse's kills), CLEANSE, SIGN, ENTER / EXIT, DARK, BLOCK
// (the first few refused hits), DEFLECT (the first few barrier shots), SLOWFX,
// BLEED, STATS every 10 s while anyone is inside, FX_DROPPED / SPAWN_FAILED /
// BARRIER_MISSING.
// =============================================================================

#using scripts\codescripts\struct;
#using scripts\shared\callbacks_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;
#using scripts\shared\ai\zombie_utility;
#using scripts\zm\_zm_score;
#using scripts\zm\_zm_utility;
#using scripts\zm\zm_tod2_cybercity\_tod_breather_data;
#using scripts\zm\zm_tod2_cybercity\_tod_zombie_speed;
#using scripts\zm\zm_tod2_cybercity\_tod_doppelghast;    // spawn_hunter / hunter_hp / valid_target (the guardians)
#using scripts\zm\zm_tod2_cybercity\_tod_mangler;        // spawn_at (the guardians)

#insert scripts\shared\shared.gsh;

#precache( "model", "tod_haven_dome" );
#precache( "model", "tod_haven_dome_pulse" );
#precache( "model", "tod_haven_dome_flash" );
#precache( "model", "tod_haven_dome_dark" );
#precache( "model", "tod_haven_dome_dark_dim" );
#precache( "model", "tod_haven_dome_dark_flash" );
#precache( "model", "tod_haven_sign_10" );
#precache( "model", "tod_haven_sign_20" );
#precache( "model", "tod_haven_sign_30" );
#precache( "model", "tod_haven_sign_40" );
#precache( "model", "tod_haven_sign_10_dark" );
#precache( "model", "tod_haven_sign_20_dark" );
#precache( "model", "tod_haven_sign_30_dark" );
#precache( "model", "tod_haven_sign_40_dark" );
#precache( "fx", "tod/haven/fx_tod_haven_ambient" );
#precache( "fx", "tod/haven/fx_tod_haven_corrupt" );
#precache( "fx", "tod/haven/fx_tod_haven_cross" );
#precache( "fx", "tod/haven/fx_tod_haven_push" );
#precache( "fx", "tod/haven/fx_tod_haven_boot" );
#precache( "fx", "tod/haven/fx_tod_haven_wake" );
#precache( "fx", "tod/haven/fx_tod_haven_guard_down" );
#precache( "fx", "tod/haven/fx_tod_haven_cleanse" );
#precache( "fx", "tod/haven/fx_tod_haven_slowed" );
#precache( "fx", "tod/haven/fx_tod_haven_deflect" );
#precache( "fx", "tod/haven/fx_tod_haven_fury" );
#precache( "fx", "tod/haven/fx_tod_haven_convulse" );
#precache( "fx", "tod/haven/fx_tod_haven_collapse" );
#precache( "eventstring", "tod_haven" );
#precache( "eventstring", "tod_haven_hit" );
#precache( "eventstring", "tod_haven_state" );
#precache( "eventstring", "tod_haven_bleed" );

#namespace tod_haven;

// --- THE FIELD'S NUMBERS (user 2026-10-02: "33% slower and 33% less damage") ---
#define TOD_HAVEN_SLOW            0.67     // an enemy inside a SAFE field moves (and swings) at this fraction of its speed
#define TOD_HAVEN_DR              0.67     // a player inside a SAFE field takes this fraction of enemy damage
#define TOD_HAVEN_KILL_PAY        0.25     // a player inside a SAFE field is paid this fraction of every kill's money (sitting in a zone costs)
#define TOD_HAVEN_BLEEDOUT        1.5      // tweak #3: a player downed inside a SAFE field bleeds out this many times slower (LOCKSTEP TodHealthTint.lua BLEED_MULT)
// THE SEALED WAY DOWN (user 2026-10-04, the first real playthrough: "You must secure the dome
// area before you move on or else door cannot be bought"): a live haven that is not yet taken
// seals its floor's way down, the enter_lap<floor> door at the foot of the hall's W flight.
// _tod_doors asks door_seal_state() (level.tod_haven_door_seal_fn) and owns the prompt and the
// refusal; a dark (unbooted) haven seals nothing, so a pre-power descent can never strand anyone.
#define TOD_HAVEN_SEAL_DOORS      1

// --- THE GUARDIANS (docs/202 v3) ---
// THE ROSTER IS THE PARTY (user 2026-10-05: "the dark dome should spawn in amount of elites as players in game"):
// one guardian per player in the game, on every floor. The first is always a Doppelghast (the haven's heart), the
// rest Manglers, and a party of TOD_HAVEN_GUARD_D2_PARTY or more raises a second Doppelghast in place of a Mangler:
// 1 player = 1D, 2 = 1D 1M, 3 = 1D 2M (the original "a Doppelghast and a couple of Manglers"), 4 = 2D 2M. The deeper
// havens are still harder: they are met later, and every guardian's health is round-zombie units (hunter_hp).
// Retired: the per-floor roster 40 1D2M / 30 1D2M / 20 2D2M / 10 2D3M and its +1 Doppelghast for 3-4 players.
#define TOD_HAVEN_GUARD_PER_PLAYER 1       // guardians per player in the game
#define TOD_HAVEN_GUARD_D2_PARTY   4       // a party this big raises its second guardian Doppelghast
#define TOD_HAVEN_GUARD_DOPPEL_UNITS 8     // a guardian Doppelghast's HP in round zombies (the round director's is 5)
#define TOD_HAVEN_GUARD_MANGLER_UNITS 6    // a guardian Mangler's (its own default is 5)
#define TOD_HAVEN_GUARD_STAGGER   0.6      // seconds between guardian spawns (each has its own ghosted tell)
#define TOD_HAVEN_GUARD_ACTOR_RESERVE 3    // never spawn a guardian with fewer free actor slots than this (the horde keeps its slots)
#define TOD_HAVEN_GUARD_RETRY     2        // seconds between spawn attempts while the pool is full
#define TOD_HAVEN_GUARD_GIVE_UP   60       // seconds of denied spawns after which the haven wants only what it has
#define TOD_HAVEN_GUARD_CLEAR     100      // prefer a spot this far from every player (the tell gives 1.2 s anyway)
#define TOD_HAVEN_FENCE_TICK      0.25     // v4: the guardians' fence test period (s) ...
#define TOD_HAVEN_FENCE_SECS      0.75     // ... a guardian outside its field this long is put back inside ...
#define TOD_HAVEN_FENCE_OUT       24       // ... "outside" = past the field's out radius by this much
#define TOD_HAVEN_SPOT_CLEAR      100      // a spot with a living player this near is not "free" to land a guardian on
#define TOD_HAVEN_CLEANSE_PTS     500      // every player's purse when a haven is taken (the elite purses were the killers')
#define TOD_HAVEN_STATE_BAND      true     // the wake / guard-down banners go to players in the leash band (false = everyone)

#define TOD_HAVEN_TICK            0.1      // membership test period (s)
#define TOD_HAVEN_WAKE_TICK       0.25     // the wake watch period (s)
// (v4: the membership's sphere, body point and z band are GENERATED: haven_in_r3 / haven_out_r3 /
// haven_body_up / haven_z_below / haven_z_above in _tod_breather_data.gsc, from tools/haven_layout.js)
#define TOD_HAVEN_DARK_IN_SECS    1.2      // v4: the darkness's breath starts this long after its swallow ...
#define TOD_HAVEN_DARK_BREATH_SECS 5.5     // ... and re-plays this often (tod_haven_dark_breath is 5.5 s, faded at both ends)
#define TOD_HAVEN_SHOT_NEAR       900      // v4: a shot fired within this of a corrupted field (2D, its floor) is traced to the barrier
#define TOD_HAVEN_SHOT_RANGE      6000     // ... this far
#define TOD_HAVEN_DEFLECT_GAP_MS  90       // per haven: a barrier-hit ripple at most this often ...
#define TOD_HAVEN_DEFLECT_SND_GAP_MS 160   // ... and its zap
#define TOD_HAVEN_LOG_FIRST       12       // the first N refused hits / barrier shots are logged (dev)
#define TOD_HAVEN_TELEPORT        120      // a move this far in one tick is a teleport: no ripple, no flash
#define TOD_HAVEN_HUD_RESEND_MS   2000     // the HUD state re-sent this often (hydrates a rebuilt HUD; never re-pulses)
#define TOD_HAVEN_BLEED_RESEND_MS 2000     // the bleed mask re-sent this often
#define TOD_HAVEN_HINT_ENTRIES    3        // the first N safe entries per player carry the "what it does" line
#define TOD_HAVEN_HIT_GAP_MS      220      // the hit flicker + tink at most this often per player
#define TOD_HAVEN_PUSH_FX_GAP_MS  250      // per haven: a zombie push-through effect at most this often
#define TOD_HAVEN_PUSH_SND_GAP_MS 400      // ... and its crackle
#define TOD_HAVEN_CROSS_GAP_MS    120      // per haven: a player crossing ripple at most this often
#define TOD_HAVEN_FLASH_MS        300      // a crossing flash: 150 ms bright, then 150 ms pulse
#define TOD_HAVEN_BEAT_MS         4800     // the safe field's heartbeat: a soft pulse this often ...
#define TOD_HAVEN_BEAT_LEN_MS     260      // ... lasting this long
#define TOD_HAVEN_SPIN_SECS       96       // one slow revolution of the lattice
#define TOD_HAVEN_FALLBACK_SECS   15       // boot any haven the power wave never reached, this long after power_on
#define TOD_HAVEN_WAVE_REACH      240      // the wave at z boots every haven with floor >= z - this
#define TOD_HAVEN_SLOW_FX_MAX     10       // slow carriers per field at once (the horde walks in by the dozen)
#define TOD_HAVEN_SLOW_FX_UP      36       // the carrier spawns this high on the body before it links to the chest bone
#define TOD_HAVEN_SLOW_FX_TAG     "j_spine4"   // the bone it rides (the repo's convention for a host on an AI: _tod_golden_zombie, _tod_sprinter)
#define TOD_HAVEN_SIGN_GLITCH_MIN 2.5      // the corrupted sign stutters every 2.5 .. 5 s (dormant) ...
#define TOD_HAVEN_SIGN_GLITCH_MAX 5.0
#define TOD_HAVEN_SIGN_GLITCH_FIGHT_MIN 0.9   // ... every 0.9 .. 2.4 s while its guardians are up (v5)
#define TOD_HAVEN_SIGN_GLITCH_FIGHT_MAX 2.4

// --- THE CORRUPTED LOOK (docs/202 v5: "the two states of the dome ... quite different") ---
#define TOD_HAVEN_RATCHET_DEG_MIN 5        // a corrupted dome turns in RATCHETS (a broken mechanism): 5 .. 14 degrees ...
#define TOD_HAVEN_RATCHET_DEG_MAX 14
#define TOD_HAVEN_RATCHET_SECS    0.22     // ... over this long ...
#define TOD_HAVEN_RATCHET_WAIT    1.6      // ... then holds this long (dormant) ...
#define TOD_HAVEN_RATCHET_WAIT_FIGHT 0.55  // ... or this long while its guardians are up
#define TOD_HAVEN_FLICKER_MIN     1.4      // the corrupted lattice BROWNS OUT (the dim skin) every 1.4 .. 4.2 s dormant ...
#define TOD_HAVEN_FLICKER_MAX     4.2
#define TOD_HAVEN_FLICKER_FIGHT_MIN 0.5    // ... every 0.5 .. 1.8 s in the fight ...
#define TOD_HAVEN_FLICKER_FIGHT_MAX 1.8
#define TOD_HAVEN_FLICKER_MS      110      // ... for this long (a dying tube)
#define TOD_HAVEN_GROAN_MIN       6.0      // the breached dome GROANS (3D, from a random point of its rim) every 6 .. 12 s dormant ...
#define TOD_HAVEN_GROAN_MAX       12.0
#define TOD_HAVEN_GROAN_FIGHT_MIN 3.0      // ... every 3 .. 6 s in the fight
#define TOD_HAVEN_GROAN_FIGHT_MAX 6.0
#define TOD_HAVEN_GROAN_UP        110      // the groan's source: this high on the field, a random bearing
#define TOD_HAVEN_DOWN_QUAKE      0.14     // a guardian's death shakes the floor this much ...
#define TOD_HAVEN_DOWN_QUAKE_SECS 0.6      // ... for this long (the purge's reach)

// --- THE PURIFICATION (docs/202 v5: "the transition of purification to be nicely animated") ---
// One timeline from the last guardian's death (purge_run): THE CONVULSION -> THE COLLAPSE -> THE BLOOM -> SETTLE.
// LOCKSTEP: tools/haven/make_fx.py and make_sounds.py READ these defines and purge_strobe_steps() out of this
// file, so the effects, the sounds and the dome's own strobe agree to the millisecond; TodHaven.lua's VOID_MS
// is the void's length in ms (test_haven.js holds both).
#define TOD_HAVEN_PURGE_CONVULSE_SECS 2.2  // the convulsion's length
#define TOD_HAVEN_PURGE_VOID_SECS 0.35     // the void: black for the players inside (LOCKSTEP TodHaven.lua VOID_MS)
#define TOD_HAVEN_PURGE_INFLATE_SECS 0.8   // the safe dome inflates over this long (ease-out) ...
#define TOD_HAVEN_PURGE_INFLATE_FROM 0.06  // ... from this scale
#define TOD_HAVEN_PURGE_SETTLE_SECS 1.2    // the bloom settles over this long, then the safe hum starts
#define TOD_HAVEN_PURGE_QUAKE     0.22     // the convulsion's quake scale ...
#define TOD_HAVEN_PURGE_QUAKE_R   1100     // ... and reach (the hall, the galleries, the flights round it)
#define TOD_HAVEN_PURGE_SLAM      0.5      // the collapse's kick (half a second)
#define TOD_HAVEN_PURGE_HUM_FADE  1.5      // the dark hum fades out over this long under the convulsion
#define TOD_HAVEN_PURGE_KILL_MARGIN 666    // the collapse kills every ordinary zombie inside with the stock nuke's idiom: health + this (a kill intent the power scale leaves alone)

#define TOD_HAVEN_FX_AMBIENT      "tod/haven/fx_tod_haven_ambient"
#define TOD_HAVEN_FX_CORRUPT      "tod/haven/fx_tod_haven_corrupt"
#define TOD_HAVEN_FX_CROSS        "tod/haven/fx_tod_haven_cross"
#define TOD_HAVEN_FX_PUSH         "tod/haven/fx_tod_haven_push"
#define TOD_HAVEN_FX_BOOT         "tod/haven/fx_tod_haven_boot"
#define TOD_HAVEN_FX_WAKE         "tod/haven/fx_tod_haven_wake"
#define TOD_HAVEN_FX_GUARD_DOWN   "tod/haven/fx_tod_haven_guard_down"
#define TOD_HAVEN_FX_CLEANSE      "tod/haven/fx_tod_haven_cleanse"
#define TOD_HAVEN_FX_SLOWED       "tod/haven/fx_tod_haven_slowed"
#define TOD_HAVEN_FX_DEFLECT      "tod/haven/fx_tod_haven_deflect"
#define TOD_HAVEN_FX_FURY         "tod/haven/fx_tod_haven_fury"       // v5: the fight's loop (replaces the corrupt loop at the wake)
#define TOD_HAVEN_FX_CONVULSE     "tod/haven/fx_tod_haven_convulse"   // v5: the purification's first beat
#define TOD_HAVEN_FX_COLLAPSE     "tod/haven/fx_tod_haven_collapse"   // v5: its second (the implosion)
#define TOD_HAVEN_SND_ENTER       "tod_haven_enter"
#define TOD_HAVEN_SND_EXIT        "tod_haven_exit"
#define TOD_HAVEN_SND_PUSH        "tod_haven_push"
#define TOD_HAVEN_SND_ABSORB      "tod_haven_absorb"
#define TOD_HAVEN_SND_IGNITE      "tod_haven_ignite"
#define TOD_HAVEN_SND_HUM         "tod_haven_hum"
#define TOD_HAVEN_SND_HUM_DARK    "tod_haven_hum_dark"
#define TOD_HAVEN_SND_WAKE        "tod_haven_wake"
#define TOD_HAVEN_SND_GUARD_DOWN  "tod_haven_guard_down"
#define TOD_HAVEN_SND_CLEANSE     "tod_haven_cleanse"
#define TOD_HAVEN_SND_DARK_IN     "tod_haven_dark_in"
#define TOD_HAVEN_SND_DARK_BREATH "tod_haven_dark_breath"
#define TOD_HAVEN_SND_DEFLECT     "tod_haven_deflect"
#define TOD_HAVEN_SND_PURGE       "tod_haven_purge"       // v5: the convulsion + the collapse, from the heart (composed to the defines above)
#define TOD_HAVEN_SND_GROAN       "tod_haven_groan"       // v5: the breached dome straining (two takes behind one alias)
#define TOD_HAVEN_SND_DARK_LIFT   "tod_haven_dark_lift"   // v5: the darkness lifting (2D, to the player it leaves)

// HUD event flags (TodHaven.lua, LOCKSTEP): bit 0 = a real crossing (play the pulse),
// bit 1 = show the "what it does" line under SAFE ZONE.
#define TOD_HAVEN_HUD_PULSE       1
#define TOD_HAVEN_HUD_HINT        2
// HUD field states (tod_haven's third argument, LOCKSTEP TodHaven.lua STATE_*)
#define TOD_HAVEN_STATE_CORRUPT   1
#define TOD_HAVEN_STATE_SAFE      2
// HUD banners (tod_haven_state's first argument, LOCKSTEP TodHaven.lua BANNER_*)
#define TOD_HAVEN_BANNER_WAKE     1
#define TOD_HAVEN_BANNER_SECURED  2        // its third argument: 1 = the player is on the haven's floor (the bigger flash)
#define TOD_HAVEN_BANNER_DOWN     3
#define TOD_HAVEN_BANNER_PURGE    4        // v5: the convulsion began (the HUD grips the veil + flickers for the players inside)
#define TOD_HAVEN_BANNER_COLLAPSE 5        // v5: the collapse (the void: black for the players inside)
#define TOD_HAVEN_BANNER_STROBE   6        // v5: one strobe of the convulsion (a red flicker for the players inside)

function init()
{
	level.tod_havens = [];
	zs = tod_breather_data::breather_zs();
	for ( i = 0; i < zs.size; i++ )
	{
		h = SpawnStruct();
		h.index = i;
		h.z = zs[ i ];
		h.center = tod_breather_data::haven_center( zs[ i ] );
		h.floor = 1 + int( zs[ i ] / 384 );
		h.live = false;
		h.safe = false;
		h.state = "dark";          // dark -> corrupt -> fight -> safe
		h.vis = "";
		h.vis_hold = false;
		h.flash_until = 0;
		h.beat_next = 0;
		h.beat_until = 0;
		h.push_fx_next = 0;
		h.push_snd_next = 0;
		h.cross_next = 0;
		h.ai_in = 0;
		h.players_in = 0;
		h.slow_fx = 0;
		h.guards = [];
		h.guards_wanted = 0;
		h.guards_spawned = 0;
		h.guards_down = 0;
		h.woke_ms = 0;
		h.flicker_next = 0;        // v5: the corrupted dome's brown-outs
		h.flicker_until = 0;
		h.purge_ms = 0;            // v5: the purification's clock and its collapse
		h.purge_kills = 0;
		h.collapsed = false;
		// v4: the field's sphere (its centre is under the floor) and the barrier (the map's brushmodel)
		h.sphere = ( h.center[ 0 ], h.center[ 1 ], h.z + tod_breather_data::haven_sphere_c() );
		h.deflect_next = 0;
		h.deflect_snd_next = 0;
		h.barrier_solid = false;
		h.barrier = GetEnt( tod_breather_data::haven_barrier_name( h.floor ), "targetname" );
		if ( isdefined( h.barrier ) )
			h.barrier NotSolid();   // the dome is dark until the power: nothing to stop yet
		else
			dev_log( "BARRIER_MISSING floor=" + h.floor + " name=" + tod_breather_data::haven_barrier_name( h.floor ) + " (an old map: bullets cross; the damage gate still holds)" );
		level.tod_havens[ i ] = h;
	}
	level.tod_haven_in_r2 = tod_breather_data::haven_in_r3() * tod_breather_data::haven_in_r3();
	level.tod_haven_out_r2 = tod_breather_data::haven_out_r3() * tod_breather_data::haven_out_r3();
	level.tod_haven_body_up = tod_breather_data::haven_body_up();
	level.tod_haven_z_below = tod_breather_data::haven_z_below();
	level.tod_haven_z_above = tod_breather_data::haven_z_above();
	level.tod_haven_stats = [];
	level.tod_haven_stats[ "enter" ] = 0;
	level.tod_haven_stats[ "exit" ] = 0;
	level.tod_haven_stats[ "ai_in" ] = 0;
	level.tod_haven_stats[ "hits" ] = 0;
	level.tod_haven_stats[ "absorbed" ] = 0;
	level.tod_haven_stats[ "kills" ] = 0;      // kills paid while the payee stood inside
	level.tod_haven_stats[ "nominal" ] = 0;    // what those kills were worth
	level.tod_haven_stats[ "paid" ] = 0;       // what they paid
	level.tod_haven_stats[ "guards" ] = 0;     // guardians spawned
	level.tod_haven_stats[ "guards_down" ] = 0;
	level.tod_haven_stats[ "cleansed" ] = 0;   // havens taken
	level.tod_haven_stats[ "slowfx" ] = 0;     // slow carriers spawned
	level.tod_haven_stats[ "slowfx_dropped" ] = 0;
	level.tod_haven_stats[ "blocked" ] = 0;     // v4: hits refused across a corrupted field's barrier
	level.tod_haven_stats[ "deflects" ] = 0;    // shots stopped on a barrier (traced)
	level.tod_haven_stats[ "fenced" ] = 0;      // guardians put back inside
	level.tod_haven_stats[ "dark" ] = 0;        // players the darkness took
	level.tod_haven_stats[ "purged" ] = 0;      // v5: ordinary zombies the collapses killed

	// the consumers outside this file read these pointers (never an import:
	// _tod_bosses and _tod_stray must not #using a module that imports them)
	level.tod_safezone_dr = &dr_for;
	level.tod_haven_inside_fn = &point_inside_live;   // _tod_stray / _tod_ambush: inside a SAFE field
	level.tod_haven_note_fn = &note_absorbed;
	level.tod_haven_kill_pay_fn = &kill_pay;           // the kill payouts (_tod_upgrades, _tod_bosses, _tod_partners, _tod_necro_summon)
	level.tod_haven_kill_preview_fn = &kill_preview;   // the score popup (_zm_aetherium_hud), read-only
	level.tod_haven_calm_fn = &calm_any;               // _tod_endless_rounds: the x1.19 rest (tweak #2)
	level.tod_haven_locked_fn = &point_locked;         // _tod_teleport / _tod_arena: a pad in a haven not yet taken is dead
	level.tod_haven_door_seal_fn = &door_seal_state;   // _tod_doors: a haven floor's way down waits for its haven (2026-10-04)
	level.tod_haven_barrier_fn = &barrier_blocks;      // _tod_bosses: enemy damage to a player across a corrupted field's barrier (v4)

	// v4 THE BARRIER'S DAMAGE GATE for enemies: wrap the actor damage front door (the power scale's
	// wrapper is already in it - main() installs it before _tod_main runs), so a hit across a corrupted
	// field's barrier never lands, whatever made it
	if ( isdefined( level.callbackActorDamage ) && !IS_TRUE( level.tod_haven_gate_installed ) )
	{
		level.tod_haven_gate_installed = true;
		level.tod_haven_prev_actor_damage = level.callbackActorDamage;
		level.callbackActorDamage = &actor_damage_gate;
	}
	// v4 THE BARRIER'S ANSWER: every player's shots are traced near a corrupted field
	callback::on_spawned( &haven_on_spawned );
	foreach ( p in GetPlayers() )
		if ( isdefined( p ) )
			p haven_on_spawned();

	level thread wave_listen();
	level thread fallback_boot();
	level thread tick();
	level thread wake_watch();
	level thread bleed_watch();
	level thread stats_watch();
	barriers = 0;
	foreach ( h in level.tod_havens )
		if ( isdefined( h.barrier ) )
			barriers++;
	dev_log( "INIT rev=5 havens=" + level.tod_havens.size + " r=" + tod_breather_data::haven_radius() + " sphere=" + tod_breather_data::haven_sphere_r()
		+ "@" + tod_breather_data::haven_sphere_c() + " in3=" + tod_breather_data::haven_in_r3() + " out3=" + tod_breather_data::haven_out_r3()
		+ " barriers=" + barriers + " gate=" + IS_TRUE( level.tod_haven_gate_installed ) + " slow=" + TOD_HAVEN_SLOW + " dr=" + TOD_HAVEN_DR + " kill_pay=" + TOD_HAVEN_KILL_PAY
		+ " bleed=" + TOD_HAVEN_BLEEDOUT + " cleanse_pts=" + TOD_HAVEN_CLEANSE_PTS + " wake_r=" + tod_breather_data::haven_wake_r()
		+ " leash_r=" + tod_breather_data::haven_leash_r() + " purge=" + TOD_HAVEN_PURGE_CONVULSE_SECS + "+" + TOD_HAVEN_PURGE_VOID_SECS + "+" + TOD_HAVEN_PURGE_INFLATE_SECS
		+ "/" + TOD_HAVEN_PURGE_SETTLE_SECS + "s strobes=" + purge_strobe_steps().size + " floors=" + floors_text() );
}

function floors_text()
{
	s = "";
	foreach ( h in level.tod_havens )
		s = s + ( ( s == "" ) ? "" : "," ) + h.floor;
	return s;
}

// -----------------------------------------------------------------------------
// POWER: the wave boots each haven as it passes; a fallback boots the rest
// -----------------------------------------------------------------------------
function wave_listen()
{
	level endon( "end_game" );
	for ( ;; )
	{
		level waittill( "tod_power_wave_z", z );
		if ( !isdefined( z ) )
			continue;
		foreach ( h in level.tod_havens )
			if ( !h.live && !IS_TRUE( h.booting ) && h.z >= z - TOD_HAVEN_WAVE_REACH )
				level thread boot( h, "wave" );
	}
}

function fallback_boot()
{
	level endon( "end_game" );
	while ( !( level flag::exists( "power_on" ) ) )
		wait 0.05;
	level flag::wait_till( "power_on" );
	wait TOD_HAVEN_FALLBACK_SECS;
	foreach ( h in level.tod_havens )
		if ( !h.live && !IS_TRUE( h.booting ) )
			level thread boot( h, "fallback" );
}

// A haven boots CORRUPTED (docs/202 v3): the crimson dome, the dark hum, the
// corrupt ambient, the red sign. Nothing it does to anyone until it is taken.
function boot( h, why )
{
	level endon( "end_game" );
	h.booting = true;
	org = ( h.center[ 0 ], h.center[ 1 ], h.z );
	dome = Spawn( "script_model", org );
	if ( !isdefined( dome ) )
	{
		h.booting = false;
		dev_log( "SPAWN_FAILED dome floor=" + h.floor + " (entity pool full)" );
		return;
	}
	dome.angles = ( 0, h.index * 37, 0 );
	dome SetModel( "tod_haven_dome_dark_flash" );
	dome NotSolid();   // a field you walk through: never a wall, never a bullet stop (the model has no collision either)
	dome Hide();
	h.dome = dome;
	wait 0.05;
	fx_at( TOD_HAVEN_FX_BOOT, org, ( 0, 0, 0 ), 3 );
	dome PlaySound( TOD_HAVEN_SND_IGNITE );
	// the boot flicker: an electrical stutter, then on
	steps = array( 0.08, 0.10, 0.06, 0.14, 0.05, 0.08 );
	for ( i = 0; i < steps.size; i++ )
	{
		if ( i % 2 == 0 )
			dome Show();
		else
			dome Hide();
		wait steps[ i ];
	}
	dome Show();
	dome SetModel( "tod_haven_dome_dark" );
	h.vis = "tod_haven_dome_dark";
	wait 0.25;
	h.live = true;
	h.state = "corrupt";
	h.booting = false;
	barrier_set( h, true );   // v4: bullets stop at the corrupted field (bodies walk through)
	dome PlayLoopSound( TOD_HAVEN_SND_HUM_DARK, 1 );
	ambient_start( h, TOD_HAVEN_FX_CORRUPT );
	dome thread spin_forever( h );
	level thread dome_visuals( h );
	level thread sign_spawn( h );
	level thread groan_loop( h );   // v5: the breached dome strains
	dev_log( "BOOT floor=" + h.floor + " why=" + why + " at=" + org + " state=corrupt guards=" + guard_count( h, "doppelghast" ) + "d/" + guard_count( h, "mangler" ) + "m" );
}

// the looping ambient on a carrier at the dome centre (the corrupt one, then the safe one)
function ambient_start( h, effect )
{
	if ( isdefined( h.fx_host ) )
		h.fx_host Delete();
	h.fx_host = undefined;
	host = Spawn( "script_model", ( h.center[ 0 ], h.center[ 1 ], h.z ) );
	if ( !isdefined( host ) )
	{
		dev_log( "FX_DROPPED ambient floor=" + h.floor + " effect=" + effect + " (entity pool full)" );
		return;
	}
	host SetModel( "tag_origin" );
	host.angles = ( 0, 0, 0 );
	h.fx_host = host;
	host thread ambient_play( effect );
}

function ambient_play( effect )   // self = the ambient carrier at the dome centre
{
	self endon( "death" );
	wait 0.05;   // a snapshot: the client resolves tag_origin on the entity first
	PlayFXOnTag( effect, self, "tag_origin" );
}

// The dome's turn. SAFE: one smooth revolution per TOD_HAVEN_SPIN_SECS. CORRUPTED (v5): a
// RATCHET - a broken mechanism turning in jerks, faster while its guardians are up; the
// purge keeps the last jerk's pace until the safe spin takes over.
function spin_forever( h )   // self = the dome
{
	self endon( "death" );
	level endon( "end_game" );
	for ( ;; )
	{
		if ( h.safe )
		{
			self RotateYaw( 360, TOD_HAVEN_SPIN_SECS );
			self waittill( "rotatedone" );
			continue;
		}
		self RotateYaw( RandomFloatRange( TOD_HAVEN_RATCHET_DEG_MIN, TOD_HAVEN_RATCHET_DEG_MAX ), TOD_HAVEN_RATCHET_SECS );
		self waittill( "rotatedone" );
		hold = TOD_HAVEN_RATCHET_WAIT;
		if ( h.state != "corrupt" )
			hold = TOD_HAVEN_RATCHET_WAIT_FIGHT;
		wait hold;
	}
}

// -> the model the dome wears for `want` (base / pulse / flash / dim) in the haven's state.
// A corrupted field has no heartbeat, a flash skin and (v5) a DIM skin for its brown-outs;
// a safe one has base / pulse / flash.
function dome_model( h, want )
{
	if ( h.safe )
	{
		if ( want == "base" || want == "dim" )
			return "tod_haven_dome";
		return "tod_haven_dome_" + want;
	}
	if ( want == "flash" )
		return "tod_haven_dome_dark_flash";
	if ( want == "dim" )
		return "tod_haven_dome_dark_dim";
	return "tod_haven_dome_dark";
}

// The dome's look: base, a heartbeat pulse every TOD_HAVEN_BEAT_MS (safe), a flash
// on a crossing / a guardian's death (bright, then pulse), a BROWN-OUT now and then
// (corrupted, v5: the dim skin for TOD_HAVEN_FLICKER_MS, more often in the fight). One
// writer per dome; SetModel only on a change (h.vis = the model worn). vis_hold = the
// purification owns the model for a moment.
function dome_visuals( h )
{
	level endon( "end_game" );
	h.beat_next = GetTime() + TOD_HAVEN_BEAT_MS;
	h.flicker_next = GetTime() + int( 1000 * TOD_HAVEN_FLICKER_MAX );
	for ( ;; )
	{
		if ( !isdefined( h.dome ) )
			return;
		if ( !h.vis_hold )
		{
			now = GetTime();
			want = "base";
			if ( now < h.flash_until )
				want = ( ( now < h.flash_until - int( TOD_HAVEN_FLASH_MS / 2 ) ) ? "flash" : "pulse" );
			else if ( h.safe )
			{
				if ( now >= h.beat_next )
				{
					h.beat_next = now + TOD_HAVEN_BEAT_MS;
					h.beat_until = now + TOD_HAVEN_BEAT_LEN_MS;
				}
				if ( now < h.beat_until )
					want = "pulse";
			}
			else
			{
				if ( now >= h.flicker_next )
				{
					h.flicker_until = now + TOD_HAVEN_FLICKER_MS;
					if ( h.state == "fight" )
						h.flicker_next = now + int( 1000 * RandomFloatRange( TOD_HAVEN_FLICKER_FIGHT_MIN, TOD_HAVEN_FLICKER_FIGHT_MAX ) );
					else
						h.flicker_next = now + int( 1000 * RandomFloatRange( TOD_HAVEN_FLICKER_MIN, TOD_HAVEN_FLICKER_MAX ) );
				}
				if ( now < h.flicker_until )
					want = "dim";
			}
			model = dome_model( h, want );
			if ( model != h.vis )
			{
				h.vis = model;
				h.dome SetModel( model );
			}
		}
		wait 0.05;
	}
}

function flash( h )
{
	h.flash_until = GetTime() + TOD_HAVEN_FLASH_MS;
}

// -----------------------------------------------------------------------------
// THE FLOOR SIGN (tweak #5): FLOOR N on the S wall, red while corrupted
// -----------------------------------------------------------------------------
function sign_model( h, dark )
{
	return "tod_haven_sign_" + h.floor + ( dark ? "_dark" : "" );
}

function sign_spawn( h )
{
	level endon( "end_game" );
	org = tod_breather_data::haven_sign_org( h.z );
	sign = Spawn( "script_model", org );
	if ( !isdefined( sign ) )
	{
		dev_log( "SPAWN_FAILED sign floor=" + h.floor + " (entity pool full)" );
		return;
	}
	sign SetModel( sign_model( h, true ) );
	sign.angles = ( 0, tod_breather_data::haven_sign_yaw(), 0 );
	sign NotSolid();
	sign Hide();
	h.sign = sign;
	wait 0.4;
	sign_flicker_on( sign );
	h.sign_dark = true;
	level thread sign_glitch( h );
	dev_log( "SIGN floor=" + h.floor + " state=dark at=" + org );
}

// the lit sign's flicker-on (the jump title's 70/60/50/100/120/50 ms stutter)
function sign_flicker_on( sign )
{
	steps = array( 0.07, 0.06, 0.05, 0.10, 0.12, 0.05 );
	for ( i = 0; i < steps.size; i++ )
	{
		if ( !isdefined( sign ) )
			return;
		if ( i % 2 == 0 )
			sign Show();
		else
			sign Hide();
		wait steps[ i ];
	}
	if ( isdefined( sign ) )
		sign Show();
}

// a corrupted sign stutters now and then (an unstable lamp; v5: more often while the
// guardians are up); ends when the purification takes the sign over (sign_glitch_done)
function sign_glitch( h )
{
	level endon( "end_game" );
	for ( ;; )
	{
		if ( h.state == "fight" )
			wait RandomFloatRange( TOD_HAVEN_SIGN_GLITCH_FIGHT_MIN, TOD_HAVEN_SIGN_GLITCH_FIGHT_MAX );
		else
			wait RandomFloatRange( TOD_HAVEN_SIGN_GLITCH_MIN, TOD_HAVEN_SIGN_GLITCH_MAX );
		if ( sign_glitch_done( h ) )
			return;
		h.sign Hide();
		wait 0.05;
		if ( sign_glitch_done( h ) )
			return;
		h.sign Show();
		wait 0.03;
		if ( sign_glitch_done( h ) )
			return;
		h.sign Hide();
		wait 0.04;
		if ( sign_glitch_done( h ) )
			return;
		h.sign Show();
	}
}

function sign_glitch_done( h )
{
	return ( h.safe || h.state == "purge" || !isdefined( h.sign ) );
}

// the bloom: the sign (dark since the collapse) flickers back in the district's colour
function sign_cleanse( h )
{
	level endon( "end_game" );
	if ( !isdefined( h.sign ) )
		return;
	h.sign Hide();
	wait 0.6;
	if ( !isdefined( h.sign ) )
		return;
	h.sign SetModel( sign_model( h, false ) );
	h.sign_dark = false;
	sign_flicker_on( h.sign );
	dev_log( "SIGN floor=" + h.floor + " state=safe" );
}

// THE GROANS (v5): the breached dome strains - a low creak from a random point of its rim,
// every TOD_HAVEN_GROAN_MIN..MAX s dormant, more often in the fight; over at the purification.
function groan_loop( h )
{
	level endon( "end_game" );
	for ( ;; )
	{
		if ( h.state == "fight" )
			wait RandomFloatRange( TOD_HAVEN_GROAN_FIGHT_MIN, TOD_HAVEN_GROAN_FIGHT_MAX );
		else
			wait RandomFloatRange( TOD_HAVEN_GROAN_MIN, TOD_HAVEN_GROAN_MAX );
		if ( h.safe || h.state == "purge" )
			return;
		if ( IS_TRUE( level.tod_upgrade_pause ) )
			continue;
		a = RandomFloatRange( 0, 360 );
		pt = field_point( h, h.center + ( cos( a ) * 100, sin( a ) * 100, 0 ), TOD_HAVEN_GROAN_UP );
		sound_at( TOD_HAVEN_SND_GROAN, pt );
	}
}

// -----------------------------------------------------------------------------
// THE GUARDIANS (docs/202 v3)
// -----------------------------------------------------------------------------
// -> how many of `kind` this haven raises: one guardian per player in the game (THE ROSTER IS THE PARTY,
// the defines), the first a Doppelghast, the rest Manglers, a second Doppelghast for a party of four. The same
// on every floor; `h` stays in the signature for the callers and the logs.
function guard_count( h, kind )
{
	party = GetPlayers().size;
	if ( party < 1 )
		party = 1;
	n = party * TOD_HAVEN_GUARD_PER_PLAYER;
	d = 1;
	if ( party >= TOD_HAVEN_GUARD_D2_PARTY )
		d = 2;
	if ( d > n )
		d = n;
	if ( kind == "doppelghast" )
		return d;
	return n - d;
}

// the wake band round the heart: the hall, its porch, the galleries over it
function in_wake_band( h, o )
{
	if ( o[ 2 ] < h.z + tod_breather_data::haven_wake_z_lo() || o[ 2 ] > h.z + tod_breather_data::haven_wake_z_hi() )
		return false;
	r = tod_breather_data::haven_wake_r();
	return ( Distance2DSquared( o, h.center ) <= r * r );
}

// the leash band: the haven's floor (its lap and the landings over it). v4: it scopes
// the wake / guard-down banners and the guardians' spawn target; their bound is the field.
function in_leash_band( h, o )
{
	if ( o[ 2 ] < h.z + tod_breather_data::haven_leash_z_lo() || o[ 2 ] > h.z + tod_breather_data::haven_leash_z_hi() )
		return false;
	r = tod_breather_data::haven_leash_r();
	return ( Distance2DSquared( o, h.center ) <= r * r );
}

function guard_target_valid( p )
{
	if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
		return false;
	if ( isdefined( p.sessionstate ) && p.sessionstate != "playing" )
		return false;
	if ( p laststand::player_is_in_laststand() )
		return false;
	return true;
}

// -> a player in the wake band of a corrupted haven (the one who wakes it), or undefined
function waker_for( h )
{
	foreach ( p in GetPlayers() )
		if ( guard_target_valid( p ) && in_wake_band( h, p.origin ) )
			return p;
	return undefined;
}

function wake_watch()
{
	level endon( "end_game" );
	for ( ;; )
	{
		wait TOD_HAVEN_WAKE_TICK;
		if ( IS_TRUE( level.tod_upgrade_pause ) )
			continue;
		foreach ( h in level.tod_havens )
		{
			if ( !h.live || h.state != "corrupt" )
				continue;
			p = waker_for( h );
			if ( isdefined( p ) )
				level thread wake( h, p );
		}
	}
}

// THE WAKE: the field convulses and its guardians rise.
function wake( h, by )
{
	if ( h.state != "corrupt" )
		return;
	h.state = "fight";
	h.woke_ms = GetTime();
	h.guards_wanted = guard_count( h, "doppelghast" ) + guard_count( h, "mangler" );
	org = ( h.center[ 0 ], h.center[ 1 ], h.z );
	fx_at( TOD_HAVEN_FX_WAKE, org, ( 0, 0, 0 ), 3 );
	sound_at( TOD_HAVEN_SND_WAKE, org );
	flash( h );
	ambient_start( h, TOD_HAVEN_FX_FURY );   // v5: the fight's frenzy replaces the dormant loop
	banner( h, TOD_HAVEN_BANNER_WAKE, h.guards_wanted );
	dev_log( "WAKE floor=" + h.floor + " by=" + by.name + " at=" + by.origin + " guards=" + guard_count( h, "doppelghast" ) + "d/" + guard_count( h, "mangler" ) + "m round=" + level.round_number );
	level thread spawn_guardians( h );
}

// Raises every guardian the haven wants, with a stagger; a denied spawn (the actor
// pool) is retried until it lands or TOD_HAVEN_GUARD_GIVE_UP s pass, after which
// the haven wants only what it has (so a full pool can never leave it untakeable).
function spawn_guardians( h )
{
	level endon( "end_game" );
	nd = guard_count( h, "doppelghast" );
	nm = guard_count( h, "mangler" );
	// the first is a Doppelghast when there is one, then they alternate while both kinds remain
	kinds = [];
	d = 0;
	m = 0;
	for ( i = 0; i < nd + nm; i++ )
	{
		if ( d < nd && ( m >= nm || i % 2 == 0 ) )
		{
			kinds[ i ] = "doppelghast";
			d++;
		}
		else
		{
			kinds[ i ] = "mangler";
			m++;
		}
	}
	started = GetTime();
	i = 0;
	while ( i < kinds.size && h.state == "fight" )
	{
		if ( IS_TRUE( level.tod_upgrade_pause ) )
		{
			wait 0.5;
			continue;
		}
		g = spawn_guard( h, kinds[ i ] );
		if ( isdefined( g ) )
		{
			i++;
			wait TOD_HAVEN_GUARD_STAGGER;
			continue;
		}
		if ( GetTime() - started > TOD_HAVEN_GUARD_GIVE_UP * 1000 )
		{
			dev_log( "GUARD_GIVE_UP floor=" + h.floor + " wanted=" + h.guards_wanted + " spawned=" + h.guards_spawned );
			h.guards_wanted = h.guards_spawned;
			break;
		}
		wait TOD_HAVEN_GUARD_RETRY;
	}
	maybe_cleanse( h );
}

// the squared distance from a point to the nearest living player (a big number with nobody alive)
function nearest_player_d2( o )
{
	near = -1;
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || !isalive( p ) )
			continue;
		d = DistanceSquared( o, p.origin );
		if ( near < 0 || d < near )
			near = d;
	}
	if ( near < 0 )
		near = 100000000;
	return near;
}

// is spot i held by a living guardian of this haven other than `me`?
function spot_taken( h, i, me )
{
	foreach ( g in h.guards )
		if ( isdefined( g ) && isalive( g ) && g !== me && isdefined( g.tod_haven_spot ) && g.tod_haven_spot == i )
			return true;
	return false;
}

// -> the index of the guardian spot to use: a FREE one (no other living guardian on it), the
// farthest from the nearest living player; every spot taken -> the farthest of all. v3 always
// chose the one spot farthest from the player, so the whole roster rose on top of each other.
function guard_spot( h, me )
{
	spots = tod_breather_data::haven_guard_spots( h.z );
	best = -1;
	best_d = -1;
	for ( pass = 0; pass < 2 && best < 0; pass++ )
	{
		for ( i = 0; i < spots.size; i++ )
		{
			if ( pass == 0 && spot_taken( h, i, me ) )
				continue;
			d = nearest_player_d2( spots[ i ] );
			if ( d > best_d )
			{
				best = i;
				best_d = d;
			}
		}
	}
	return best;
}

// -> the nearest valid player on the haven's floor, else any valid player
function guard_target( h )
{
	best = undefined;
	best_d = 0;
	foreach ( p in GetPlayers() )
	{
		if ( !tod_doppelghast::valid_target( p ) )
			continue;
		d = Distance2DSquared( p.origin, h.center );
		if ( !in_leash_band( h, p.origin ) )
			d += 100000000;   // off the floor: last resort
		if ( !isdefined( best ) || d < best_d )
		{
			best = p;
			best_d = d;
		}
	}
	return best;
}

// Spawns ONE guardian of `kind` inside the field. -> the actor, or undefined
// (denied: the actor reserve, no target, SpawnActor).
function spawn_guard( h, kind )
{
	if ( GetFreeActorCount() < TOD_HAVEN_GUARD_ACTOR_RESERVE )
	{
		dev_log( "GUARD_DENIED floor=" + h.floor + " kind=" + kind + " why=actor_reserve free=" + GetFreeActorCount() );
		return undefined;
	}
	target = guard_target( h );
	if ( !isdefined( target ) )
	{
		dev_log( "GUARD_DENIED floor=" + h.floor + " kind=" + kind + " why=no_target" );
		return undefined;
	}
	spot = guard_spot( h, undefined );
	org = tod_breather_data::haven_guard_spots( h.z )[ spot ];
	facing = VectorToAngles( target.origin - org );
	if ( kind == "mangler" )
	{
		actor = tod_mangler::spawn_at( org, target, ( 0, facing[ 1 ], 0 ) );
		if ( isdefined( actor ) )
		{
			actor.health = tod_doppelghast::hunter_hp( TOD_HAVEN_GUARD_MANGLER_UNITS );
			actor.maxhealth = actor.health;
		}
	}
	else
		actor = tod_doppelghast::spawn_hunter( org, target, TOD_HAVEN_GUARD_DOPPEL_UNITS );
	if ( !isdefined( actor ) )
	{
		dev_log( "GUARD_DENIED floor=" + h.floor + " kind=" + kind + " why=spawn_failed" );
		return undefined;
	}
	actor.tod_haven_guard = h.index;
	actor.tod_haven_guard_kind = kind;
	actor.tod_haven_spot = spot;                   // its own spot round the field (v4: one each)
	actor.tod_hunt_home = org;                     // where it stands when nobody is inside its field
	actor.tod_hunt_filter = &guard_target_ok;      // it hunts players INSIDE its field only (_tod_doppelghast / _tod_mangler hunt_target)
	actor.tod_reloc_fn = &guard_reloc;             // a stuck relocation lands inside its field (_tod_doppelghast::reloc_point)
	h.guards[ h.guards.size ] = actor;
	h.guards_spawned++;
	level.tod_haven_stats[ "guards" ]++;
	level thread guard_watch( h, actor, kind );
	actor thread guard_fence( h );
	dev_log( "GUARD_SPAWN floor=" + h.floor + " kind=" + kind + " hp=" + actor.health + " spot=" + spot + " at=" + org + " target=" + target.name + " n=" + h.guards_spawned + "/" + h.guards_wanted + " free_actors=" + GetFreeActorCount() );
	return actor;
}

// self = a guardian (called by the elite modules' hunt_target through
// self.tod_hunt_filter): may it hunt this player? v4: only one INSIDE its field
// (the player's membership, ticked with hysteresis); anyone else is out of its reach.
function guard_target_ok( p )
{
	if ( !isdefined( self.tod_haven_guard ) || !isdefined( level.tod_havens ) )
		return true;
	h = level.tod_havens[ self.tod_haven_guard ];
	if ( !isdefined( h ) || !isdefined( p ) )
		return true;
	if ( isdefined( p.tod_haven ) )
		return ( p.tod_haven == h.index );
	return ( haven_at( p.origin, -1 ) == h.index );
}

// is a guardian's body inside its field, with the fence's slack (out radius + TOD_HAVEN_FENCE_OUT)?
function fence_inside( h, o )
{
	if ( o[ 2 ] < h.z - level.tod_haven_z_below || o[ 2 ] > h.z + level.tod_haven_z_above )
		return false;
	r = tod_breather_data::haven_out_r3() + TOD_HAVEN_FENCE_OUT;
	return ( DistanceSquared( o + ( 0, 0, level.tod_haven_body_up ), h.sphere ) <= r * r );
}

// self = a guardian -> where it goes when put back: its own spot, unless a living player
// stands on it (then a free spot away from them; its home follows)
function guard_home( h )
{
	spots = tod_breather_data::haven_guard_spots( h.z );
	if ( isdefined( self.tod_haven_spot ) && nearest_player_d2( spots[ self.tod_haven_spot ] ) > TOD_HAVEN_SPOT_CLEAR * TOD_HAVEN_SPOT_CLEAR )
		return spots[ self.tod_haven_spot ];
	i = guard_spot( h, self );
	self.tod_haven_spot = i;
	self.tod_hunt_home = spots[ i ];
	return spots[ i ];
}

// self = a guardian (_tod_doppelghast::reloc_point asks it, for both elites, when it is stuck):
// -> a spot INSIDE its field, never a navmesh point near its target outside it
function guard_reloc( target )
{
	if ( !isdefined( self.tod_haven_guard ) || !isdefined( level.tod_havens ) )
		return undefined;
	h = level.tod_havens[ self.tod_haven_guard ];
	if ( !isdefined( h ) )
		return undefined;
	org = self guard_home( h );
	dev_log( "GUARD_RELOC floor=" + h.floor + " kind=" + self.tod_haven_guard_kind + " to=" + org );
	return org;
}

// THE FENCE (v4: "the elites are not allowed to leave the dome"). self = a guardian: outside its
// field for TOD_HAVEN_FENCE_SECS -> put back on its spot. Its targets are all inside (the filter),
// so this catches only a leap or a chase that carried it over the rim.
function guard_fence( h )
{
	self endon( "death" );
	level endon( "end_game" );
	away = 0;
	for ( ;; )
	{
		wait TOD_HAVEN_FENCE_TICK;
		if ( h.safe )
			return;
		if ( IS_TRUE( level.tod_upgrade_pause ) )
			continue;
		if ( fence_inside( h, self.origin ) )
		{
			away = 0;
			continue;
		}
		if ( IS_TRUE( self.tod_bo6_attacking ) || IS_TRUE( self.tod_mangler_attacking ) || IS_TRUE( self.tod_bo6_juking ) )
			continue;
		away += TOD_HAVEN_FENCE_TICK;
		if ( away < TOD_HAVEN_FENCE_SECS )
			continue;
		self guard_fence_now( h );
		away = 0;
	}
}

function guard_fence_now( h )   // self = a guardian outside its field
{
	from = self.origin;
	to = self guard_home( h );
	self ForceTeleport( to );
	self.tod_motion_start = to;   // the modules' own "a teleport is not locomotion" stamp
	level.tod_haven_stats[ "fenced" ]++;
	fx_at( TOD_HAVEN_FX_GUARD_DOWN, to + ( 0, 0, 40 ), ( 0, 0, 0 ), 2 );
	dev_log( "GUARD_FENCE floor=" + h.floor + " kind=" + self.tod_haven_guard_kind + " from=" + from + " to=" + to + " spot=" + self.tod_haven_spot );
}

function guard_watch( h, g, kind )
{
	level endon( "end_game" );
	g waittill( "death", attacker );
	killer = "none";
	if ( isdefined( attacker ) && isplayer( attacker ) )
		killer = attacker.name;
	guard_down( h, kind, killer );
}

// A guardian fell: the dome cracks red, the count comes down, the last one cleanses.
function guard_down( h, kind, killer )
{
	if ( h.safe )
		return;
	h.guards_down++;
	level.tod_haven_stats[ "guards_down" ]++;
	left = guards_left( h );
	org = ( h.center[ 0 ], h.center[ 1 ], h.z );
	if ( left > 0 )
	{
		fx_at( TOD_HAVEN_FX_GUARD_DOWN, org, ( 0, 0, 0 ), 2 );
		sound_at( TOD_HAVEN_SND_GUARD_DOWN, org );
		Earthquake( TOD_HAVEN_DOWN_QUAKE, TOD_HAVEN_DOWN_QUAKE_SECS, org, TOD_HAVEN_PURGE_QUAKE_R );   // v5: the floor feels it
		flash( h );
		banner( h, TOD_HAVEN_BANNER_DOWN, left );
		hud_refresh_inside( h );
	}
	dev_log( "GUARD_DOWN floor=" + h.floor + " kind=" + kind + " killer=" + killer + " down=" + h.guards_down + " left=" + left + " round=" + level.round_number );
	maybe_cleanse( h );
}

// -> guardians still to kill (those not yet raised count: the haven is not taken by killing the first)
function guards_left( h )
{
	left = h.guards_wanted - h.guards_down;
	if ( left < 0 )
		left = 0;
	return left;
}

function maybe_cleanse( h )
{
	if ( h.safe || h.state != "fight" || IS_TRUE( h.cleanse_due ) )
		return;
	if ( h.guards_spawned < h.guards_wanted )
		return;   // still raising them
	if ( h.guards_down < h.guards_wanted )
		return;
	h.cleanse_due = true;
	level thread cleanse( h );
}

// -----------------------------------------------------------------------------
// THE PURIFICATION (docs/202 v5): the last guardian fell - the haven is the party's
// -----------------------------------------------------------------------------
// THE STROBE SCHEDULE (ms from the convulsion's start): accelerating toward the collapse.
// tools/haven/make_fx.py (the heart's flashes) and make_sounds.py (the clicks) READ this
// list, so a change here moves all three together (test_haven.js holds its order and
// its end inside the convulsion).
function purge_strobe_steps()
{
	return array( 0, 470, 860, 1190, 1460, 1680, 1860, 2010, 2130 );
}

// THE ENTRY: the state turns "purge" at once (no second cleanse; the wake watch and the
// guardians' fence stand down; the field is NOT safe through the convulsion and its
// barrier still stands) and THE CONVULSION begins - the effect and the sound (both
// composed to the defines), the quake, the dark hum fading out, the HUD's grip for the
// players inside. The timeline runs on its own thread (purge_run).
function cleanse( h )
{
	if ( h.safe || h.state == "purge" )
		return;
	h.state = "purge";
	h.purge_ms = GetTime();
	org = ( h.center[ 0 ], h.center[ 1 ], h.z );
	fx_at( TOD_HAVEN_FX_CONVULSE, org, ( 0, 0, 0 ), TOD_HAVEN_PURGE_CONVULSE_SECS + 1 );
	sound_at( TOD_HAVEN_SND_PURGE, org );
	Earthquake( TOD_HAVEN_PURGE_QUAKE, TOD_HAVEN_PURGE_CONVULSE_SECS, org, TOD_HAVEN_PURGE_QUAKE_R );
	if ( isdefined( h.dome ) )
		h.dome StopLoopSound( TOD_HAVEN_PURGE_HUM_FADE );
	banner( h, TOD_HAVEN_BANNER_PURGE, 0 );
	dev_log( "PURGE floor=" + h.floor + " phase=convulse secs=" + TOD_HAVEN_PURGE_CONVULSE_SECS + " guards=" + h.guards_down + " round=" + level.round_number );
	level thread purge_run( h );
}

// the timeline: convulse -> collapse -> void -> bloom -> inflate -> settle
function purge_run( h )
{
	level endon( "end_game" );
	level thread dome_convulse( h );
	wait TOD_HAVEN_PURGE_CONVULSE_SECS;
	collapse( h );
	wait TOD_HAVEN_PURGE_VOID_SECS;
	purify( h );
	level thread dome_inflate( h );
	wait TOD_HAVEN_PURGE_SETTLE_SECS;
	if ( isdefined( h.dome ) )
		h.dome PlayLoopSound( TOD_HAVEN_SND_HUM, 1 );
	dev_log( "PURGE floor=" + h.floor + " phase=settled total_ms=" + ( GetTime() - h.purge_ms ) );
}

// the convulsion on the dome itself: its skin strobes on purge_strobe_steps() (the flash
// skin for 70 ms, then the dark or the dim skin), the sign goes out on each strobe, and
// the players inside get the strobe (a red flicker in step with the dome and the clicks)
function dome_convulse( h )
{
	level endon( "end_game" );
	h.vis_hold = true;
	steps = purge_strobe_steps();
	start = GetTime();
	for ( i = 0; i < steps.size; i++ )
	{
		while ( GetTime() < start + steps[ i ] )
			wait 0.05;
		if ( IS_TRUE( h.collapsed ) )
			return;
		strobe_tell( h, i );
		if ( isdefined( h.dome ) )
			h.dome SetModel( "tod_haven_dome_dark_flash" );
		if ( isdefined( h.sign ) )
			h.sign Hide();
		wait 0.07;
		if ( IS_TRUE( h.collapsed ) )
			return;
		if ( isdefined( h.dome ) )
			h.dome SetModel( ( ( i % 2 == 0 ) ? "tod_haven_dome_dark" : "tod_haven_dome_dark_dim" ) );
		if ( isdefined( h.sign ) )
			h.sign Show();
	}
}

// the players inside see each strobe (TodHaven.lua flickers red for it)
function strobe_tell( h, i )
{
	foreach ( p in GetPlayers() )
		if ( isdefined( p ) && isdefined( p.tod_haven ) && p.tod_haven == h.index )
			p LuiNotifyEvent( &"tod_haven_state", 3, TOD_HAVEN_BANNER_STROBE, h.floor, i );
}

// 2. THE COLLAPSE (wait-free): the field implodes - the dome and the barrier GO, every
// ordinary zombie inside dies, the players inside see black for the void
// (TOD_HAVEN_BANNER_COLLAPSE). Once per haven.
function collapse( h )
{
	if ( h.safe || IS_TRUE( h.collapsed ) )
		return;
	h.collapsed = true;
	org = ( h.center[ 0 ], h.center[ 1 ], h.z );
	fx_at( TOD_HAVEN_FX_COLLAPSE, org, ( 0, 0, 0 ), 3 );
	Earthquake( TOD_HAVEN_PURGE_SLAM, 0.5, org, TOD_HAVEN_PURGE_QUAKE_R + 100 );
	if ( isdefined( h.dome ) )
	{
		h.vis_hold = true;
		h.dome Hide();   // gone for the void; the bloom inflates it back (dome_inflate)
	}
	if ( isdefined( h.sign ) )
		h.sign Hide();   // dark until the bloom's flicker-on (sign_cleanse)
	barrier_set( h, false );   // v4: "then bullets can shoot through and kill things both ways"
	h.purge_kills = purge_zombies( h );
	banner( h, TOD_HAVEN_BANNER_COLLAPSE, 0 );
	dev_log( "PURGE floor=" + h.floor + " phase=collapse kills=" + h.purge_kills + " ms=" + ( GetTime() - h.purge_ms ) );
}

// -> how many ordinary zombies the collapse killed: every one inside the field (its ticked
// membership, or where it stands), never an elite (the directors' Doppelghasts / Manglers,
// anything with an elite bar kind) and never a guardian; with the stock nuke's idiom -
// health + the margin, no attacker: nobody is paid, and the power scale leaves a kill intent
// alone (tod_ps_exempt round it: the repo's rule for health-derived damage).
function purge_zombies( h )
{
	n = 0;
	team = ( isdefined( level.zombie_team ) ? level.zombie_team : "axis" );
	foreach ( ai in GetAITeamArray( team ) )
	{
		if ( !isdefined( ai ) || !isalive( ai ) || !( ai zombie_utility::is_zombie() ) )
			continue;
		if ( isdefined( ai.tod_boss_kind ) || isdefined( ai.tod_haven_guard ) || IS_TRUE( ai.tod_doppelghast ) || IS_TRUE( ai.tod_mangler ) )
			continue;
		idx = -1;
		if ( isdefined( ai.tod_haven_ai ) )
			idx = ai.tod_haven_ai;
		else
			idx = haven_at( ai.origin, -1 );
		if ( idx != h.index )
			continue;
		ai.tod_ps_exempt = true;
		ai DoDamage( ai.health + TOD_HAVEN_PURGE_KILL_MARGIN, ai.origin );
		if ( isdefined( ai ) )
			ai.tod_ps_exempt = undefined;
		n++;
	}
	level.tod_haven_stats[ "purged" ] += n;
	return n;
}

// 3. THE BLOOM (wait-free): the field is SAFE from this instant - the bloom effect + chord,
// the safe ambient, FLOOR N HAVEN SECURED to everyone (the bigger flash for the floor), the
// purse, the members, the slow; the sign flickers back in the district's colour.
function purify( h )
{
	if ( h.safe )
		return;
	h.safe = true;
	h.state = "safe";
	h.collapsed = true;
	barrier_set( h, false );   // (down since the collapse; a direct purify() keeps the contract)
	level.tod_haven_stats[ "cleansed" ]++;
	secs = ( ( h.woke_ms > 0 ) ? int( ( GetTime() - h.woke_ms ) / 1000 ) : 0 );
	org = ( h.center[ 0 ], h.center[ 1 ], h.z );
	fx_at( TOD_HAVEN_FX_CLEANSE, org, ( 0, 0, 0 ), 4 );
	sound_at( TOD_HAVEN_SND_CLEANSE, org );
	ambient_start( h, TOD_HAVEN_FX_AMBIENT );
	banner( h, TOD_HAVEN_BANNER_SECURED, 0 );
	level thread sign_cleanse( h );
	// the purse
	paid = 0;
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || ( isdefined( p.sessionstate ) && p.sessionstate != "playing" ) )
			continue;
		p zm_score::add_to_player_score( TOD_HAVEN_CLEANSE_PTS );
		paid++;
	}
	// everyone inside is a member of a safe field from this instant; every enemy inside is slowed
	players_in = 0;
	foreach ( p in GetPlayers() )
	{
		if ( isdefined( p ) && isdefined( p.tod_haven ) && p.tod_haven == h.index )
		{
			p player_enter( h, true );
			players_in++;
		}
	}
	ai_in = 0;
	team = ( isdefined( level.zombie_team ) ? level.zombie_team : "axis" );
	foreach ( ai in GetAITeamArray( team ) )
	{
		if ( !isdefined( ai ) || !isalive( ai ) || !isdefined( ai.tod_haven_ai ) || ai.tod_haven_ai != h.index )
			continue;
		ai.tod_safe_mult = TOD_HAVEN_SLOW;
		ai apply_rate();
		ai slow_fx_start( h );
		ai_in++;
	}
	dev_log( "CLEANSE floor=" + h.floor + " secs=" + secs + " guards=" + h.guards_down + " purge_kills=" + h.purge_kills + " pay=" + TOD_HAVEN_CLEANSE_PTS + "x" + paid + " players_in=" + players_in + " ai_in=" + ai_in + " round=" + level.round_number );
}

// the safe dome INFLATES from a point (SetScale on the dome, eased out) in the flash skin,
// then flash -> pulse -> base through dome_visuals
function dome_inflate( h )
{
	level endon( "end_game" );
	if ( !isdefined( h.dome ) )
		return;
	h.vis_hold = true;
	h.dome SetModel( "tod_haven_dome_flash" );
	h.dome SetScale( TOD_HAVEN_PURGE_INFLATE_FROM );
	h.dome Show();
	steps = int( TOD_HAVEN_PURGE_INFLATE_SECS * 20 + 0.5 );
	for ( i = 1; i <= steps; i++ )
	{
		wait 0.05;
		if ( !isdefined( h.dome ) )
			return;
		t = ( i + 0.0 ) / steps;
		k = 1 - ( 1 - t ) * ( 1 - t ) * ( 1 - t );
		h.dome SetScale( TOD_HAVEN_PURGE_INFLATE_FROM + ( 1 - TOD_HAVEN_PURGE_INFLATE_FROM ) * k );
	}
	h.dome SetScale( 1 );
	h.vis = "";
	h.vis_hold = false;
	h.flash_until = GetTime() + 600;
}

// a HUD banner (tod_haven_state) to the players it concerns: the wake, a guardian down
// and the purification's beats to the players on that floor (TOD_HAVEN_STATE_BAND),
// SECURED to everyone - its third argument says whether THEY are on the floor (v5: the
// bigger flash for those who took it)
function banner( h, kind, left )
{
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) )
			continue;
		near = in_leash_band( h, p.origin );
		if ( kind != TOD_HAVEN_BANNER_SECURED && TOD_HAVEN_STATE_BAND && !near )
			continue;
		arg = left;
		if ( kind == TOD_HAVEN_BANNER_SECURED )
			arg = ( ( near ) ? 1 : 0 );
		p LuiNotifyEvent( &"tod_haven_state", 3, kind, h.floor, arg );
	}
}

// re-send the field state to everyone inside (the guardians-left count moved)
function hud_refresh_inside( h )
{
	foreach ( p in GetPlayers() )
		if ( isdefined( p ) && isdefined( p.tod_haven ) && p.tod_haven == h.index )
			p hud_send( true, 0 );
}

// -----------------------------------------------------------------------------
// MEMBERSHIP
// -----------------------------------------------------------------------------
// -> the haven index a body at origin `o` is inside, or -1. v4: the field's SPHERE - the
// point haven_body_up() over the origin within the in radius of the sphere's centre (its
// centre is under the floor), inside the z band round the floor. `cur` (the body's
// current haven, or -1) widens it to the out radius for its own haven (hysteresis). Any
// LIVE haven counts (the HUD shows a corrupted field too); the gameplay effects ask h.safe.
function haven_at( o, cur )
{
	foreach ( h in level.tod_havens )
	{
		if ( !h.live )
			continue;
		if ( o[ 2 ] < h.z - level.tod_haven_z_below || o[ 2 ] > h.z + level.tod_haven_z_above )
			continue;
		r2 = ( ( cur == h.index ) ? level.tod_haven_out_r2 : level.tod_haven_in_r2 );
		if ( DistanceSquared( o + ( 0, 0, level.tod_haven_body_up ), h.sphere ) <= r2 )
			return h.index;
	}
	return -1;
}

// PUBLIC (level.tod_haven_inside_fn): is this point inside a live, SAFE field? The
// hunt (_tod_stray) never relocates a zombie into one; the ambush never plans one
// there. A corrupted hall is a fight zone: the horde may rise in it.
function point_inside_live( o )
{
	if ( !isdefined( o ) || !isdefined( level.tod_havens ) )
		return false;
	idx = haven_at( o, -1 );
	if ( idx < 0 )
		return false;
	return level.tod_havens[ idx ].safe;
}

// PUBLIC (level.tod_haven_locked_fn; _tod_teleport, _tod_arena): is a pad / gate at
// this point inside a haven that is not yet taken? (The hall box, not the field:
// a dead pad reads as dead from the whole hall.)
function point_locked( o )
{
	if ( !isdefined( o ) || !isdefined( level.tod_havens ) )
		return false;
	j = tod_breather_data::lounge_index_at( o );
	if ( j < 0 || !isdefined( level.tod_havens[ j ] ) )
		return false;
	return !level.tod_havens[ j ].safe;
}

// PUBLIC (level.tod_haven_door_seal_fn; _tod_doors): -1 = this door is no haven floor's way
// down, 1 = it is and its haven is live and not yet taken (SEALED), 0 = it is and it may be
// bought (the haven is taken, or still dark before the power). Wait-free and pure.
function door_seal_state( flag )
{
	if ( !TOD_HAVEN_SEAL_DOORS || !isdefined( flag ) || !isdefined( level.tod_havens ) )
		return -1;
	foreach ( h in level.tod_havens )
	{
		if ( flag != "enter_lap" + h.floor )
			continue;
		if ( h.safe )
			return 0;
		if ( h.live || IS_TRUE( h.booting ) )
			return 1;
		return 0;
	}
	return -1;
}

// PUBLIC (level.tod_haven_calm_fn; _tod_endless_rounds): is any living player
// standing INSIDE a safe field right now? (tweak #2: the rest is the sanctuary,
// not the hall round it)
function calm_any()
{
	if ( !isdefined( level.tod_havens ) )
		return false;
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || !isalive( p ) || !isdefined( p.tod_haven ) || p.tod_haven < 0 )
			continue;
		h = level.tod_havens[ p.tod_haven ];
		if ( isdefined( h ) && h.safe )
			return true;
	}
	return false;
}

function tick()
{
	level endon( "end_game" );
	for ( ;; )
	{
		wait TOD_HAVEN_TICK;
		live_any = false;
		foreach ( h in level.tod_havens )
			if ( h.live )
				live_any = true;
		if ( !live_any )
			continue;
		now = GetTime();
		foreach ( h in level.tod_havens )
		{
			h.players_in = 0;
			h.ai_in = 0;
		}
		players = GetPlayers();
		foreach ( p in players )
			if ( isdefined( p ) )
				p player_update( now );
		team = ( isdefined( level.zombie_team ) ? level.zombie_team : "axis" );
		ais = GetAITeamArray( team );
		foreach ( ai in ais )
			if ( isdefined( ai ) && isalive( ai ) )
				ai ai_update( now );
	}
}

// self = a player
function player_update( now )
{
	if ( !isdefined( self.tod_haven ) )
		self.tod_haven = -1;
	o = self.origin;
	cur = self.tod_haven;
	idx = -1;
	if ( self.sessionstate === "playing" )
		idx = haven_at( o, cur );
	moved = 0;
	if ( isdefined( self.tod_haven_last ) )
		moved = Distance( o, self.tod_haven_last );
	self.tod_haven_last = o;
	if ( idx >= 0 )
		level.tod_havens[ idx ].players_in++;

	if ( idx != cur )
	{
		self.tod_haven = idx;
		teleported = ( !isdefined( self.tod_haven_seen ) || moved > TOD_HAVEN_TELEPORT || self.sessionstate !== "playing" );
		self.tod_haven_seen = true;
		if ( idx >= 0 )
			self player_enter( level.tod_havens[ idx ], teleported );
		else
			self player_exit( level.tod_havens[ cur ], teleported );
		self.tod_haven_hud_next = now + TOD_HAVEN_HUD_RESEND_MS;
		return;
	}
	self.tod_haven_seen = true;
	if ( !isdefined( self.tod_haven_hud_next ) || now >= self.tod_haven_hud_next )
	{
		self.tod_haven_hud_next = now + TOD_HAVEN_HUD_RESEND_MS;
		self hud_send( ( idx >= 0 ), 0 );
	}
}

// Entering a field. SAFE: the kill tax, the bleed-out grace, the ripple + sound, the
// cyan tint, SAFE ZONE. CORRUPTED: the red tint and CORRUPTED HAVEN only - the evil
// field does nothing to you and shows no field feedback of its own.
function player_enter( h, teleported )
{
	if ( !h.safe )
	{
		self.tod_haven_pay = undefined;
		self bleed_set( false );
		self hud_send( true, TOD_HAVEN_HUD_PULSE );
		self dark_set( true );   // v4: the darkness takes you (TodHaven.lua draws the veil off the CORRUPTED state)
		level.tod_haven_stats[ "enter" ]++;
		dev_log( "ENTER player=" + self.name + " floor=" + h.floor + " state=" + h.state + " at=" + self.origin + " teleported=" + teleported + " left=" + guards_left( h ) );
		return;
	}
	self dark_set( false );   // a safe field: the darkness is gone (the cleanse lands here for everyone inside)
	if ( !isdefined( self.tod_haven_entries ) )
		self.tod_haven_entries = 0;
	self.tod_haven_entries++;
	self.tod_haven_pay = TOD_HAVEN_KILL_PAY;   // THE KILL PAY: every kill payout to this player reads it while they stay
	self bleed_set( true );
	flags = TOD_HAVEN_HUD_PULSE;
	if ( self.tod_haven_entries <= TOD_HAVEN_HINT_ENTRIES )
		flags = flags + TOD_HAVEN_HUD_HINT;
	self hud_send( true, flags );
	level.tod_haven_stats[ "enter" ]++;
	if ( !teleported )
		cross_feedback( h, self.origin, TOD_HAVEN_SND_ENTER );
	dev_log( "ENTER player=" + self.name + " floor=" + h.floor + " state=safe at=" + self.origin + " teleported=" + teleported + " entries=" + self.tod_haven_entries + " kill_pay=" + TOD_HAVEN_KILL_PAY + " bleed=" + TOD_HAVEN_BLEEDOUT );
}

function player_exit( h, teleported )
{
	was_safe = ( isdefined( h ) && h.safe );
	self.tod_haven_pay = undefined;   // full kill money again (death and a teleport out land here too)
	self bleed_set( false );
	self dark_set( false );           // v4: the darkness lifts as you leave
	self hud_send( false, ( ( teleported || self.sessionstate !== "playing" || !was_safe ) ? 0 : TOD_HAVEN_HUD_PULSE ) );
	level.tod_haven_stats[ "exit" ]++;
	if ( !teleported && was_safe )
		cross_feedback( h, self.origin, TOD_HAVEN_SND_EXIT );
	floor = ( isdefined( h ) ? h.floor : -1 );
	dev_log( "EXIT player=" + self.name + " floor=" + floor + " at=" + self.origin + " teleported=" + teleported + " state=" + self.sessionstate );
}

// tod_haven( inside, flags, state, left ): the field's state and, while corrupted,
// how many guardians are left to kill (TodHaven.lua draws exactly this)
function hud_send( inside, flags )
{
	state = 0;
	left = 0;
	if ( inside && isdefined( self.tod_haven ) && self.tod_haven >= 0 )
	{
		h = level.tod_havens[ self.tod_haven ];
		state = ( h.safe ? TOD_HAVEN_STATE_SAFE : TOD_HAVEN_STATE_CORRUPT );
		if ( !h.safe )
			left = guards_left( h );
	}
	self LuiNotifyEvent( &"tod_haven", 4, ( inside ? 1 : 0 ), flags, state, left );
}

// The ripple + flash + sound where a player crosses: on the field above the ring
// point nearest them, facing out along the field.
function cross_feedback( h, o, snd )
{
	now = GetTime();
	if ( now < h.cross_next )
		return;
	h.cross_next = now + TOD_HAVEN_CROSS_GAP_MS;
	pt = field_point( h, o, 48 );
	fx_at( TOD_HAVEN_FX_CROSS, pt, VectorToAngles( field_normal( h, pt ) ), 2 );
	sound_at( snd, pt );
	flash( h );
}

// the point on the field nearest `o`, `up` above the floor; and the field's outward normal there
function field_point( h, o, up )
{
	d = ( o[ 0 ] - h.center[ 0 ], o[ 1 ] - h.center[ 1 ], 0 );
	if ( LengthSquared( d ) < 1 )
		d = ( 1, 0, 0 );
	d = VectorNormalize( d );
	zc = tod_breather_data::haven_sphere_c();
	rs = tod_breather_data::haven_sphere_r();
	dz = up - zc;
	r = sqrt( Max( rs * rs - dz * dz, 1 ) );
	return ( h.center[ 0 ] + d[ 0 ] * r, h.center[ 1 ] + d[ 1 ] * r, h.z + up );
}

function field_normal( h, pt )
{
	return VectorNormalize( pt - h.sphere );
}

// -----------------------------------------------------------------------------
// THE DARKNESS (v4): heard while you stand inside a corrupted field
// -----------------------------------------------------------------------------
// self = a player. On: the swallow (tod_haven_dark_in) and the breath loop. Off: the
// loop stops, both sounds are cut and the LIFT is heard (v5: the darkness leaving you,
// on the way out and at the bloom alike). Idempotent both ways. The veil itself is the
// HUD's (TodHaven.lua, off the CORRUPTED state this module already sends).
function dark_set( on )
{
	if ( on )
	{
		if ( IS_TRUE( self.tod_haven_dark ) )
			return;
		self.tod_haven_dark = true;
		level.tod_haven_stats[ "dark" ]++;
		self PlayLocalSound( TOD_HAVEN_SND_DARK_IN );
		self thread dark_breath();
		dev_log( "DARK player=" + self.name + " on" );
		return;
	}
	if ( !IS_TRUE( self.tod_haven_dark ) )
		return;
	self.tod_haven_dark = false;
	self notify( "tod_haven_dark_off" );
	self StopLocalSound( TOD_HAVEN_SND_DARK_BREATH );
	self StopLocalSound( TOD_HAVEN_SND_DARK_IN );
	self PlayLocalSound( TOD_HAVEN_SND_DARK_LIFT );
	dev_log( "DARK player=" + self.name + " off" );
}

// the breath re-played back to back while the darkness holds (never through a world pause)
function dark_breath()   // self = a player
{
	self endon( "disconnect" );
	self endon( "tod_haven_dark_off" );
	level endon( "end_game" );
	wait TOD_HAVEN_DARK_IN_SECS;
	for ( ;; )
	{
		if ( IS_TRUE( level.tod_upgrade_pause ) )
		{
			wait 0.5;
			continue;
		}
		self PlayLocalSound( TOD_HAVEN_SND_DARK_BREATH );
		wait TOD_HAVEN_DARK_BREATH_SECS;
	}
}

// -----------------------------------------------------------------------------
// THE BARRIER (v4): "bullets cannot go in or outside the dome. Until its a safe zone"
// -----------------------------------------------------------------------------
function barrier_set( h, on )
{
	h.barrier_solid = on;
	if ( !isdefined( h.barrier ) )
		return;
	if ( on )
		h.barrier Solid();
	else
		h.barrier NotSolid();
	dev_log( "BARRIER floor=" + h.floor + " solid=" + on );
}

// -> the haven index an entity counts as standing in, for the barrier (-1 = none). A guardian
// always counts as inside its own field; a player or a ticked enemy uses its membership
// (hysteresis); anything else is tested where it stands.
function side_of( ent )
{
	if ( isdefined( ent.tod_haven_guard ) )
		return ent.tod_haven_guard;
	if ( isplayer( ent ) && isdefined( ent.tod_haven ) )
		return ent.tod_haven;
	if ( isdefined( ent.tod_haven_ai ) )
		return ent.tod_haven_ai;
	if ( !isdefined( ent.origin ) )
		return -1;
	return haven_at( ent.origin, -1 );
}

// PUBLIC (level.tod_haven_barrier_fn; _tod_bosses' damage lane, and the actor gate below): does
// a CORRUPTED field's barrier stand between `attacker` and `victim`? (one in, one out)
function barrier_blocks( attacker, victim )
{
	if ( !isdefined( attacker ) || !isdefined( victim ) || attacker == victim || !isdefined( level.tod_havens ) )
		return false;
	a = side_of( attacker );
	v = side_of( victim );
	if ( a == v )
		return false;
	if ( a >= 0 && level.tod_havens[ a ].live && !level.tod_havens[ a ].safe )
		return true;
	if ( v >= 0 && level.tod_havens[ v ].live && !level.tod_havens[ v ].safe )
		return true;
	return false;
}

// THE ACTOR DAMAGE GATE (level.callbackActorDamage): a hit across a corrupted field's barrier
// never lands (no damage, no reaction, no points); every other hit goes on down the chain.
function actor_damage_gate( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, vDamageOrigin, timeOffset, boneIndex, modelIndex, surfaceType, surfaceNormal )
{
	if ( barrier_blocks( eAttacker, self ) )
	{
		level.tod_haven_stats[ "blocked" ]++;
		if ( level.tod_haven_stats[ "blocked" ] <= TOD_HAVEN_LOG_FIRST )
			dev_log( "BLOCK victim=" + self GetEntityNumber() + " attacker=" + eAttacker GetEntityNumber() + " dmg=" + iDamage + " mod=" + sMeansOfDeath + " n=" + level.tod_haven_stats[ "blocked" ] );
		return;
	}
	self [[ level.tod_haven_prev_actor_damage ]]( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, vDamageOrigin, timeOffset, boneIndex, modelIndex, surfaceType, surfaceNormal );
}

// -----------------------------------------------------------------------------
// THE BARRIER'S ANSWER (v4): a crimson ripple + a zap where a shot stops on it
// -----------------------------------------------------------------------------
function haven_on_spawned()   // self = a player (callback::on_spawned)
{
	if ( IS_TRUE( self.tod_haven_shot_watch ) )
		return;
	self.tod_haven_shot_watch = true;
	self thread shot_watch();
}

// -> the solid-barrier haven whose floor this point is on, within TOD_HAVEN_SHOT_NEAR (2D), or undefined
function barrier_near( o )
{
	foreach ( h in level.tod_havens )
	{
		if ( !h.barrier_solid || !isdefined( h.barrier ) )
			continue;
		if ( o[ 2 ] < h.z - level.tod_haven_z_below - 64 || o[ 2 ] > h.z + level.tod_haven_z_above + 400 )
			continue;
		if ( Distance2DSquared( o, h.center ) <= TOD_HAVEN_SHOT_NEAR * TOD_HAVEN_SHOT_NEAR )
			return h;
	}
	return undefined;
}

function shot_watch()   // self = a player; lives for the match (only a disconnect ends it)
{
	self endon( "disconnect" );
	level endon( "end_game" );
	for ( ;; )
	{
		self waittill( "weapon_fired" );
		h = barrier_near( self.origin );
		if ( !isdefined( h ) )
			continue;
		eye = self GetEye();
		trace = BulletTrace( eye, eye + AnglesToForward( self GetPlayerAngles() ) * TOD_HAVEN_SHOT_RANGE, false, self );
		if ( isdefined( trace[ "entity" ] ) && trace[ "entity" ] == h.barrier )
			deflect_feedback( h, trace[ "position" ], self );
	}
}

function deflect_feedback( h, pos, shooter )
{
	now = GetTime();
	level.tod_haven_stats[ "deflects" ]++;
	if ( level.tod_haven_stats[ "deflects" ] <= TOD_HAVEN_LOG_FIRST )
		dev_log( "DEFLECT floor=" + h.floor + " by=" + shooter.name + " at=" + pos + " n=" + level.tod_haven_stats[ "deflects" ] );
	if ( now < h.deflect_next )
		return;
	h.deflect_next = now + TOD_HAVEN_DEFLECT_GAP_MS;
	fx_at( TOD_HAVEN_FX_DEFLECT, pos, VectorToAngles( field_normal( h, pos ) ), 1 );
	if ( now >= h.deflect_snd_next )
	{
		h.deflect_snd_next = now + TOD_HAVEN_DEFLECT_SND_GAP_MS;
		sound_at( TOD_HAVEN_SND_DEFLECT, pos );
	}
}

// -----------------------------------------------------------------------------
// THE BLEED-OUT GRACE (tweak #3): slower bleed-out inside a safe field
// -----------------------------------------------------------------------------
// self = a player. Stock reads self.n_bleedout_time_multiplier at the down
// (_zm_laststand::PlayerLastStand), and ends an over-long bleed-out early if the
// multiplier vanishes mid-down, so a player downed inside keeps it until they are
// up again (bleed_release_after_down) even if the membership drains.
function bleed_set( on )
{
	if ( on )
	{
		if ( IS_TRUE( self.tod_haven_bleed ) )
			return;
		self.tod_haven_bleed = true;
		self.tod_haven_bleed_prev = self.n_bleedout_time_multiplier;
		base = ( isdefined( self.n_bleedout_time_multiplier ) ? self.n_bleedout_time_multiplier : 1.0 );
		self.n_bleedout_time_multiplier = base * TOD_HAVEN_BLEEDOUT;
		dev_log( "BLEED player=" + self.name + " on mult=" + self.n_bleedout_time_multiplier );
		return;
	}
	if ( !IS_TRUE( self.tod_haven_bleed ) )
		return;
	if ( self laststand::player_is_in_laststand() )
	{
		if ( !IS_TRUE( self.tod_haven_bleed_hold ) )
			self thread bleed_release_after_down();
		return;
	}
	bleed_clear();
}

function bleed_clear()   // self = a player
{
	self.tod_haven_bleed = false;
	self.n_bleedout_time_multiplier = self.tod_haven_bleed_prev;
	self.tod_haven_bleed_prev = undefined;
	dev_log( "BLEED player=" + self.name + " off" );
}

function bleed_release_after_down()   // self = a downed player who left the field (or whose field drained)
{
	self endon( "disconnect" );
	level endon( "end_game" );
	self.tod_haven_bleed_hold = true;
	while ( isdefined( self ) && self laststand::player_is_in_laststand() )
		wait 0.5;
	if ( isdefined( self ) )
		self bleed_release_check();
}

// up again: the grace goes unless they stand inside a safe field by now
function bleed_release_check()   // self = a player
{
	self.tod_haven_bleed_hold = false;
	if ( isdefined( self.tod_haven ) && self.tod_haven >= 0 && level.tod_havens[ self.tod_haven ].safe )
		return;
	bleed_clear();
}

// the HUD's bleed bars read a four-player mask (bit = entity number): sent to
// everyone on a change and every TOD_HAVEN_BLEED_RESEND_MS
function bleed_watch()
{
	level endon( "end_game" );
	last = -1;
	next = 0;
	for ( ;; )
	{
		wait 0.25;
		mask = 0;
		foreach ( p in GetPlayers() )
		{
			if ( !isdefined( p ) || !IS_TRUE( p.tod_haven_bleed ) )
				continue;
			n = p GetEntityNumber();
			if ( n >= 0 && n < 4 )
				mask = mask | ( 1 << n );
		}
		now = GetTime();
		if ( mask == last && now < next )
			continue;
		last = mask;
		next = now + TOD_HAVEN_BLEED_RESEND_MS;
		foreach ( p in GetPlayers() )
			if ( isdefined( p ) )
				p LuiNotifyEvent( &"tod_haven_bleed", 1, mask );
	}
}

// -----------------------------------------------------------------------------
// ENEMIES: the slow (safe fields), made visible
// -----------------------------------------------------------------------------
// self = an enemy AI
function ai_update( now )
{
	cur = ( isdefined( self.tod_haven_ai ) ? self.tod_haven_ai : -1 );
	idx = haven_at( self.origin, cur );
	if ( idx >= 0 )
		level.tod_havens[ idx ].ai_in++;
	if ( idx == cur )
	{
		// INSIDE, STILL: an elite with a stamped base rate gets its composed rate
		// re-asserted every tick — its other writers (the drop reveal, a Fury's
		// bamf, a web expiry) write a bare base and would drop the field's slow.
		if ( idx >= 0 && isdefined( self.tod_safe_mult ) && isdefined( self.tod_elite_base_rate ) )
			self reassert_elite();
		return;
	}
	self.tod_haven_ai = idx;
	safe = ( idx >= 0 && level.tod_havens[ idx ].safe );
	if ( safe )
		self.tod_safe_mult = TOD_HAVEN_SLOW;
	else
		self.tod_safe_mult = undefined;
	self apply_rate();
	if ( safe )
	{
		level.tod_haven_stats[ "ai_in" ]++;
		if ( !IS_TRUE( self.in_the_ground ) )
			push_feedback( level.tod_havens[ idx ], self.origin );
		self slow_fx_start( level.tod_havens[ idx ] );
	}
	else
		self slow_fx_stop();
}

// Re-apply the AI's rate NOW with the field's factor in (or out). Every lane
// already multiplies tod_safe_mult in; this only saves the wait for the sweep.
function apply_rate()
{
	if ( self zombie_utility::is_zombie() )
	{
		if ( !( self tod_zombie_speed::under_anim_slow() ) )
			self tod_zombie_speed::apply_speed_for_round( tod_zombie_speed::current_round() );
	}
	if ( isdefined( self.tod_elite_base_rate ) )
		self reassert_elite();
	// the Doppelghast / Mangler chase loops read tod_safe_mult on their next 0.25 s beat
}

function reassert_elite()
{
	if ( self tod_zombie_speed::elite_rate_owned() )
		return;
	if ( IS_TRUE( self.isTraveling ) )
		return;   // a Fury mid-teleport keeps its own traversal rate
	self ASMSetAnimationRate( self tod_zombie_speed::elite_rate_now() );
}

// self = an enemy inside a safe field: a small carrier linked to it plays the
// slowed crackle (tweak #1) - at most TOD_HAVEN_SLOW_FX_MAX per field at once
function slow_fx_start( h )
{
	if ( isdefined( self.tod_haven_slow_host ) )
		return;
	if ( h.slow_fx >= TOD_HAVEN_SLOW_FX_MAX )
	{
		level.tod_haven_stats[ "slowfx_dropped" ]++;
		return;
	}
	host = Spawn( "script_model", self.origin + ( 0, 0, TOD_HAVEN_SLOW_FX_UP ) );
	if ( !isdefined( host ) )
	{
		level.tod_haven_stats[ "slowfx_dropped" ]++;
		dev_log( "FX_DROPPED slowed floor=" + h.floor + " (entity pool full)" );
		return;
	}
	host SetModel( "tag_origin" );
	host.angles = ( 0, 0, 0 );
	// the chest bone every AI rig here carries (the golden zombie's aura, the sprinter's and the
	// Doppelghast's own torso reads all use it): the carrier rides the body, not its feet
	host LinkTo( self, TOD_HAVEN_SLOW_FX_TAG, ( 0, 0, 0 ), ( 0, 0, 0 ) );
	self.tod_haven_slow_host = host;
	self.tod_haven_slow_h = h;
	h.slow_fx++;
	level.tod_haven_stats[ "slowfx" ]++;
	host thread slow_fx_play( self, h );
	dev_log( "SLOWFX floor=" + h.floor + " n=" + h.slow_fx + " on=" + self GetEntityNumber() );
}

function slow_fx_play( owner, h )   // self = the slow carrier
{
	self endon( "death" );
	level endon( "end_game" );
	wait 0.05;
	PlayFXOnTag( TOD_HAVEN_FX_SLOWED, self, "tag_origin" );
	// ride until the enemy dies or is deleted (the field's own exit deletes the carrier first)
	while ( isdefined( owner ) && isalive( owner ) )
		wait 0.25;
	if ( isdefined( owner ) )
	{
		owner.tod_haven_slow_host = undefined;
		owner.tod_haven_slow_h = undefined;
	}
	h.slow_fx--;
	self Delete();
}

function slow_fx_stop()   // self = an enemy leaving a safe field (its carrier goes with it)
{
	if ( !isdefined( self.tod_haven_slow_host ) )
		return;
	host = self.tod_haven_slow_host;
	self.tod_haven_slow_host = undefined;
	if ( isdefined( self.tod_haven_slow_h ) )
		self.tod_haven_slow_h.slow_fx--;
	self.tod_haven_slow_h = undefined;
	if ( isdefined( host ) )
		host Delete();
}

function push_feedback( h, o )
{
	now = GetTime();
	if ( now >= h.push_fx_next )
	{
		h.push_fx_next = now + TOD_HAVEN_PUSH_FX_GAP_MS;
		pt = field_point( h, o, 40 );
		fx_at( TOD_HAVEN_FX_PUSH, pt, VectorToAngles( field_normal( h, pt ) ), 2 );
		if ( now >= h.push_snd_next )
		{
			h.push_snd_next = now + TOD_HAVEN_PUSH_SND_GAP_MS;
			sound_at( TOD_HAVEN_SND_PUSH, pt );
		}
	}
}

// -----------------------------------------------------------------------------
// THE DAMAGE CUT (level.tod_safezone_dr; _tod_bosses reads it in both lanes)
// -----------------------------------------------------------------------------
// -> the multiplier for enemy damage on this player right now. A hit that lands
// while a SAFE field holds also flickers their screen tint and plays the tink (at
// most every TOD_HAVEN_HIT_GAP_MS), so the cut is felt, not just computed.
function dr_for( player )
{
	if ( !isdefined( player ) || !isdefined( player.tod_haven ) || player.tod_haven < 0 )
		return 1.0;
	h = level.tod_havens[ player.tod_haven ];
	if ( !isdefined( h ) || !h.live || !h.safe )
		return 1.0;
	level.tod_haven_stats[ "hits" ]++;
	now = GetTime();
	if ( !isdefined( player.tod_haven_hit_next ) || now >= player.tod_haven_hit_next )
	{
		player.tod_haven_hit_next = now + TOD_HAVEN_HIT_GAP_MS;
		player LuiNotifyEvent( &"tod_haven_hit", 1, 1 );
		player PlaySoundToPlayer( TOD_HAVEN_SND_ABSORB, player );
	}
	return TOD_HAVEN_DR;
}

// PUBLIC (_tod_bosses): count the damage the field took off, for the STATS line.
function note_absorbed( amount )
{
	if ( isdefined( level.tod_haven_stats ) && isdefined( amount ) && amount > 0 )
		level.tod_haven_stats[ "absorbed" ] += amount;
}

// -----------------------------------------------------------------------------
// THE KILL PAY (level.tod_haven_kill_pay_fn / level.tod_haven_kill_preview_fn)
// -----------------------------------------------------------------------------
// -> what a kill worth `points` pays this player now. Outside a safe field:
// `points`, untouched. Inside: TOD_HAVEN_KILL_PAY of it, BANKED. Stock rounds every
// award UP to ten (zm_score::add_to_player_score), so a flat quarter of a 60-point
// kill would pay 20, a third; the bank keeps the remainder and pays exact tens, so
// over a stay the player is paid exactly the quarter (BOUNTY's own banking,
// _tod_upgrades::on_class_gun_kill). Stock kill money is banked BEFORE stock's
// Double Points, which still applies on top; a lump (the elite purse) is banked
// after its own multipliers.
function kill_pay( player, points )
{
	if ( !isdefined( player ) || !isdefined( player.tod_haven_pay ) || !isdefined( points ) || points <= 0 )
		return points;
	if ( !isdefined( player.tod_haven_bank ) )
		player.tod_haven_bank = 0;
	player.tod_haven_bank += points * player.tod_haven_pay;
	pay = int( player.tod_haven_bank / 10 ) * 10;
	player.tod_haven_bank -= pay;
	if ( isdefined( level.tod_haven_stats ) )
	{
		level.tod_haven_stats[ "kills" ]++;
		level.tod_haven_stats[ "nominal" ] += points;
		level.tod_haven_stats[ "paid" ] += pay;
	}
	return pay;
}

// READ-ONLY twin for the score popup: what kill_pay is about to pay for a kill worth
// `points`. Reads the same bank and changes nothing, so the popup shows the money
// the kill really banks and can never move the economy.
function kill_preview( player, points )
{
	if ( !isdefined( player ) || !isdefined( player.tod_haven_pay ) || !isdefined( points ) || points <= 0 )
		return points;
	bank = 0;
	if ( isdefined( player.tod_haven_bank ) )
		bank = player.tod_haven_bank;
	return int( ( bank + points * player.tod_haven_pay ) / 10 ) * 10;
}

// -----------------------------------------------------------------------------
// carriers (the proven server route: _tod_lucky::fx_at)
// -----------------------------------------------------------------------------
function fx_at( effect, org, angles, life )
{
	host = Spawn( "script_model", org );
	if ( !isdefined( host ) )
	{
		dev_log( "FX_DROPPED effect=" + effect + " at=" + org + " (entity pool full)" );
		return;
	}
	host SetModel( "tag_origin" );
	host.angles = angles;
	host thread fx_at_play( effect, life );
}

function fx_at_play( effect, life )   // self = the carrier
{
	self endon( "death" );
	wait 0.05;
	PlayFXOnTag( effect, self, "tag_origin" );
	wait life;
	self Delete();
}

function sound_at( alias, org )
{
	ent = Spawn( "script_origin", org );
	if ( !isdefined( ent ) )
		return;
	ent PlaySound( alias );
	ent thread delete_after( 5 );
}

function delete_after( secs )
{
	wait secs;
	if ( isdefined( self ) )
		self Delete();
}

// -----------------------------------------------------------------------------
// logs
// -----------------------------------------------------------------------------
function stats_watch()
{
	level endon( "end_game" );
	for ( ;; )
	{
		wait 10;
		busy = "";
		foreach ( h in level.tod_havens )
			if ( h.live && ( h.players_in > 0 || h.ai_in > 0 ) )
				busy = busy + " floor" + h.floor + "=" + h.players_in + "p/" + h.ai_in + "ai/" + h.state;
		if ( busy == "" )
			continue;
		s = level.tod_haven_stats;
		dev_log( "STATS" + busy + " enter=" + s[ "enter" ] + " exit=" + s[ "exit" ] + " ai_in=" + s[ "ai_in" ] + " hits=" + s[ "hits" ] + " absorbed=" + s[ "absorbed" ]
			+ " kills_in=" + s[ "kills" ] + " nominal=" + s[ "nominal" ] + " paid=" + s[ "paid" ] + " guards=" + s[ "guards" ] + "/" + s[ "guards_down" ]
			+ " cleansed=" + s[ "cleansed" ] + " purged=" + s[ "purged" ] + " slowfx=" + s[ "slowfx" ] + "/" + s[ "slowfx_dropped" ]
			+ " blocked=" + s[ "blocked" ] + " deflects=" + s[ "deflects" ] + " fenced=" + s[ "fenced" ] + " dark=" + s[ "dark" ] );
	}
}

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_HAVEN] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
