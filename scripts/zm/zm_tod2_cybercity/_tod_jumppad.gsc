// =============================================================================
// _tod_jumppad.gsc — THE JUMP PAD (docs/163): the only way out of the crown.
//
// User 2026-09-24: "at the ... there's a bridge that goes from the tower to
// the crown. This entire bridge most of like 80% of it needs to be removed and
// there needs to be a jump pad from one side to the other ... it'll trigger as
// soon as you walk onto it ... the player should be launched through the sky."
//
// THE GEOMETRY is gen_tower_map.js's (CW_CUT, section 5c): the causeway keeps
// a stub at each end and 5200 units of sky between them. The pad stands on the
// crown's stub (the LAUNCH deck, outside the Fall gate); the party comes down
// on the terrace's stub (the LANDING deck). Every coordinate here is read from
// GENERATED _tod_crown_data.gsc (jumppad_*), already mirrored for the crown's
// parity — none is typed in this file.
//
// ONE WAY, BY DESIGN. The Fall goes down: there is no pad back up, and the
// Fall gate seals once every living player has crossed (_tod_fall, which
// counts a player still in the air as not yet out).
//
// THE MACHINE IS DER EISENDRACHE'S JUMP PAD (2026-10-03, docs/163 s9; the user:
// "The jump pad on this map is a teleporter but I want it to have the jump pad
// model from der eisendrache. Can we switch it over with same functionality").
// It wore the teleporter until then. Now it is DE's JUMPSPHERE, installed from the
// T7 pack by tools/jumppad/install_de_jumppad.py: the broken-open half-sphere
// machine (TOD_JUMPPAD_MODEL_FRAME) over its lit deck (_DECK_OFF dark until the
// power, _DECK_ON blue), turned so its doorway faces the bridge corridor and its
// open side faces the flight (DE's own arrangement); its collision is the
// generator's `jump pad shell` clip ring (no collision on the model itself), and
// the trigger (jumppad_trigger_r, 40) is the inside of the machine: walk in, go.
// The landing deck has DE's landing pad (_LAND_OFF / _LAND_ON) with the four
// set-down spots on it. The presentation is DE's flinger's: its crackle + fling
// burst at the pad, the whoosh and the electric trail on the rider, the landing
// pad's glow while anyone is inbound, the dust + thud at the touch-down. The
// flight itself (the arc, the hang clock, the opening scene, every guard below)
// is unchanged.
//
// THE FLIGHT IS SCRIPTED, NOT THROWN. The player is linked to a tag_origin
// mover that walks a parabola in TOD_JUMPPAD_STEP MoveTo segments and is set
// down exactly on a landing spot. A velocity launch (SetVelocity) would hand
// the landing to air control and the engine's gravity: a player could strafe
// off the arc into 19,000 units of air, and a ~2000-unit drop onto the deck is
// fall damage no perk in this map fully forgives. Linked, the player can look
// around and shoot the whole way; nothing they press changes where they land.
//
// THE HANG (docs/196, user 2026-09-29: "we need the jump pad to have more hang
// time so players can feel that they are entering the real map now"). The arc's
// SHAPE is the same parabola as ever (test_jumppad sweeps exactly this shape
// against every brush), only higher (TOD_JUMPPAD_APEX) and walked on a warped
// clock, hang_u(): a punchy launch (1.6x the mean speed), a float over the apex
// (0.5x), a dive, and a soft catch at the deck (0.25x) instead of the old
// 1,950 u/s slam. Every flight is TOD_JUMPPAD_FLIGHT_SECS; a player's FIRST
// flight is TOD_JUMPPAD_CINE_SECS and is THE OPENING SCENE (below).
//
// THE OPENING SCENE (docs/196, user 2026-09-29: "rotate the skybox so that the
// tower of doom sign shows on the right and the camera can force the player to
// view it like an opening scene but only on the first time they use the jump
// pad"). The sky's title sign sits due WEST, i.e. on the RIGHT of a flight that
// runs due south. WHERE the sky puts it was MEASURED on the user's second play
// (docs/196 §3): the engine turns the whole sky by the SSI's sun azimuth PLUS the
// material's skyRotation, the image's centre column facing yaw -(sun + skyRotation)
// - roll = -(140 + 40) - 0 = 180 (LOCKSTEP with sky3d_stats.json "roll",
// tod_skybox.gdt skyRotation and BOTH SSIs' yaw / pitch, gated by test_jumppad; the
// 15:33 build's skyRotation 180 put the sign at yaw 40, behind the rider's left).
// On a player's first flight: letterbox + no HUD (TodJumpCine.lua, veil key
// "jump"), the gun is lowered, the camera locks on the rider's OWN view at the
// launch (the mover is set to that view, then PlayerLinkToDelta with no view
// arc: nothing jumps) and ONE eased path turns it to the sign and later back
// down (THE CAMERA PATH, cine_cam_angles, stepped with the arc every server
// frame), the descent's first music band is already
// playing (since 2026-09-29 it starts the moment a player steps onto this
// balcony, _tod_atmosphere::balcony_player; the reveal's "tod_jump_title" is
// only its fallback cue).
// THE CRASH (docs/196 §4, user 2026-09-29: "the skybox sign is like dimmed then
// there are two of the spaceships going at each other ... they crash into each
// other they do a huge explosion so you can't see anything and then behind is
// actually the tower of doom sign all lit up completely bright"): the camera
// settles on the DARKENED sign with two of session 9c's gunships in a standoff
// in front of it; they charge, meet nose to nose, the screen flashes white, a
// fireball fills the frame and burns, and the sign BLAZES on behind it; as the
// fire and the smoke over the sign clear, the title emerges all lit up and the
// shot holds on it, then swings back down to the tower and opens the clamp
// before the touch-down (user 2026-09-29, after the first play: "the kaboom
// ended early ... make sure sign doesnt light up until explosion happens" and
// "if we need the jump to last longer you can do that": the first flight went
// 11.0 -> 13.8 s for a real standoff, a visible fireball and time on the title).
// THE SIGN, FOURTH PASS (2026-09-30, docs/196 §6; the user: "the sign to not glow and actually be very dull and
// then after explosion it should glow very bright"): the sky's sign is BAKED DULL (build_city.py --sign-state
// dull), so it is dull from the first frame with nothing hiding it; the LIT sign is a client card model that
// flickers on at the reveal and stays lit (the smoke veil is retired). The beats below are unchanged.
// The flyer's CLIENT plays the ships, the fireball, the lit sign card and its glows
// and their sounds (_tod_jump_title.csc); this file sends it the beats
// (util::clientNotify on the jumper only: tod_jump_title_start / _ships /
// _impact / _ignite / _end) and owns the camera, the white-out, the shake and
// the rumble. A card deal or any menu freeze mid-scene tears it down at once
// (cine_wait); every exit path runs cine_end (which sends _end). Session 9c's
// sky fleet salutes the blazing sign from tod_jump_title_ignite.
//
// WHAT A FLYER IS SPARED — each one a stock system that would otherwise act
// on a player hanging over the void (the flag is self.tod_jumppad_flying):
//   * stock's OUT-OF-PLAYABLE-AREA kill (_zm.gsc player_out_of_playable_area
//     _monitor, a 3 s poll): the arc is outside every zone volume for ~6 s, so
//     level.player_out_of_playable_area_monitor_callback answers "spare" for a
//     flyer and defers to any earlier callback otherwise;
//   * DAMAGE: a player damage callback inserted FIRST in stock's chain
//     (check_player_damage_callbacks returns the first answer that is not -1)
//     returns 0 for a flyer — a down while linked to a mover is the one state
//     this file never wants to meet;
//   * TARGETING: zm_utility::increment_ignoreme for the flight (stock's
//     reference count; paired exactly once in finish()), and _tod_bosses'
//     anchor helpers skip flyers, so no elite spawn is ever queried around a
//     point in mid-air;
//   * the player-moving features: the bat lunge and ATHLETE both
//     refuse while the flag is set (a one-line field check in each).
//
// DIAGNOSTICS: [TOD_JUMPPAD] INIT / STATE (the machine lights at the power) /
// LAUNCH / LAND / REFUSE / ABORT / FX_FAIL and the scene's CINE_START / CINE_CAM (the camera path: the rider's view, the sign,
// the landing view) / CINE_TURN / CINE_REVEAL / CINE_RETURN / CINE_FREE (the
// camera's angles when control comes back) / CINE_END (with why) lines. TOD_JUMPPAD_LOG 1 prints WITHOUT the dev flag for
// the first playtests (the user tests dev-OFF builds, like _tod_fall's
// TOD_FALL_LOG) — zero it before a publish. REFUSE lines are throttled per player.
// =============================================================================

#using scripts\codescripts\struct;
#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_utility;
#using scripts\zm\_zm_zonemgr;
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;     // GENERATED: jumppad_* anchors
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;   // play_sound_at_origin (host-based, proven)

#insert scripts\shared\shared.gsh;

// THE MACHINE (docs/163 s9): Der Eisendrache's jump pad, installed by tools/jumppad/install_de_jumppad.py
#precache( "model", "tod_jumppad_frame" );
#precache( "model", "tod_jumppad_deck_off" );
#precache( "model", "tod_jumppad_deck_on" );
#precache( "model", "tod_jumppad_land_off" );
#precache( "model", "tod_jumppad_land_on" );
#precache( "fx", "dlc1/castle/fx_elec_jumppad" );
#precache( "fx", "dlc1/castle/fx_elec_jumppad_player_trail" );
#precache( "fx", "dlc1/castle/fx_elec_landingpad_glow" );
#precache( "fx", "dlc1/castle/fx_dust_landingpad" );
// THE OPENING SCENE's screen half (TodJumpCine.lua). A LuiNotifyEvent name must
// be a precached eventstring or the event silently never fires.
#precache( "eventstring", "tod_jump_cine" );

#define TOD_JUMPPAD_MODEL_FRAME    "tod_jumppad_frame"      // DE's jumpsphere machine (static, no collision: the generator's shell ring is its body)
#define TOD_JUMPPAD_MODEL_DECK_OFF "tod_jumppad_deck_off"   // its deck, the lights dark (DE's plain state): before the power
#define TOD_JUMPPAD_MODEL_DECK_ON  "tod_jumppad_deck_on"    // its deck, the lights blue (DE's ready state): from the power on
#define TOD_JUMPPAD_MODEL_LAND_OFF "tod_jumppad_land_off"   // DE's landing pad on the landing deck, dark
#define TOD_JUMPPAD_MODEL_LAND_ON  "tod_jumppad_land_on"    // ... and blue
// DE's flinger effects (dlc1/castle, real effects in the tools root - not stubs; every one is a FINITE burst: its
// looping elements carry spawn counts, so a host lives exactly as long as below and nothing needs stopping)
#define TOD_JUMPPAD_FX_LAUNCH      "dlc1/castle/fx_elec_jumppad"              // the fling: arcs + flash at the pad (~2-4 s)
#define TOD_JUMPPAD_FX_LAUNCH_SECS 4.5
#define TOD_JUMPPAD_FX_TRAIL       "dlc1/castle/fx_elec_jumppad_player_trail" // on the rider's mover for the climb (~1.2 s)
#define TOD_JUMPPAD_FX_GLOW        "dlc1/castle/fx_elec_landingpad_glow"      // the landing pad lights up for an inbound rider (~2.8 s a pulse)
#define TOD_JUMPPAD_FX_GLOW_EVERY  2.4                                        // re-pulsed while any flight is in the air
#define TOD_JUMPPAD_FX_GLOW_SECS   3.4
#define TOD_JUMPPAD_FX_DUST        "dlc1/castle/fx_dust_landingpad"           // the touch-down (~2 s)
#define TOD_JUMPPAD_FX_DUST_SECS   3.0
// DE's flinger sounds, mastered for this map's mix (sound/aliases/tod_jump.csv, 3D)
#define TOD_JUMPPAD_SND_CHARGE     "tod_jumppad_charge"   // the machine crackles: when it wakes at the power, and as it fires
#define TOD_JUMPPAD_SND_LAUNCH     "tod_jumppad_launch"   // the fling, on the rider's mover
#define TOD_JUMPPAD_SND_LAND       "tod_jumppad_land"     // the thud at the touch-down
#define TOD_JUMPPAD_FLIGHT_SECS  7.0     // launch -> set-down, every flight (4.5 until 2026-09-29: "more hang time")
#define TOD_JUMPPAD_CINE_SECS    12.1    // a player's FIRST flight: the opening scene needs the air (9.5 until the crash, 11.0 until the
                                         // standoff / visible fireball / title hold, 13.8 for the fourth pass; 11.6 for the fifth: the
                                         // user after playing the fourth: "things happen a bit too slow ... waiting at each step"; 12.1
                                         // since 2026-10-01: the 11.6 s arc + CINE_DWELL at the top, below)
// THE DWELL (2026-10-01, the user: "The pause mid air jump scene should last another 500ms before going down"): a first
// flight walks the SAME arc on the SAME hang clock (CINE_SECS - CINE_DWELL long), with CINE_DWELL seconds slipped in
// smoothly round the apex (cine_arc_frac: a raised-cosine slow-down, never a stop). Nothing before the dwell moves (the
// crash is framed on the arc up to the ignite), and from its end the flight is the old one 0.5 s later: the rider is on
// the same point of the arc at the swing back as before (test_jumppad and test_jump_title replay it).
#define TOD_JUMPPAD_CINE_DWELL      0.5  // s added at the top of a first flight
#define TOD_JUMPPAD_CINE_DWELL_AT   5.27 // s from the launch: the dwell's middle = the apex (hang_u 0.5 at 5.02 s of the arc) + DWELL / 2
#define TOD_JUMPPAD_CINE_DWELL_SPAN 2.6  // s the slow-down is spread over (3.97 .. 6.57: after the ignite, before the swing back);
                                         // the arc's own pace dips to 1 - 2 x DWELL / SPAN = 0.62 at the apex
#define TOD_JUMPPAD_APEX         2600    // how far the arc climbs above the straight line between the decks (2200 until 2026-09-29)
#define TOD_JUMPPAD_STEP         0.05    // the arc is sampled once per server frame (0.1 until 2026-09-29: the slow apex needs the finer walk)
#define TOD_JUMPPAD_LOOKAHEAD    2       // THE TRAJECTORY FIX (fifth pass, 2026-09-30; the user: "when you're going down he's kind of
                                         // wavering up and down ... clunky"): every frame the mover is aimed at the arc point this many
                                         // frames AHEAD over that many frames, so the trajectory the client extrapolates always outlives
                                         // the 50 ms snapshot interval. A one-frame segment (the fourth pass) ends exactly when the next
                                         // snapshot is due: whenever the client's clock ran a hair ahead it clamped the stale segment and
                                         // jumped on the next one - invisible against the sky on the way up, a judder against the terrace
                                         // on the way down. The path is the same curve (the mover reaches each frame's point within a
                                         // fraction of a unit: the TRACK log measures it); the camera path takes the same lookahead.
// THE HANG CLOCK: u(t) = t + A sin(360t)/2pi - B (cos(360t) - 1)/2pi + C sin(720t)/4pi
// - D (cos(720t) - 1)/4pi + L (t - t^2), the integral of the speed profile
// s(t) = 1 + A cos + B sin + C cos2 + D sin2 + L (1 - 2t), so u(1) = 1 for ANY
// values. These give s = 1.60 at launch, 0.50 at mid-flight, 0.25 at the deck,
// monotonic throughout (test_jumppad replays the formula and proves it).
#define TOD_JUMPPAD_WARP_A       ( 0.2125 )
#define TOD_JUMPPAD_WARP_B       ( -0.4 )
#define TOD_JUMPPAD_WARP_C       ( -0.2875 )
#define TOD_JUMPPAD_WARP_D       ( -0.3 )
#define TOD_JUMPPAD_WARP_L       ( 0.675 )
#define TOD_JUMPPAD_TWO_PI       6.283185307
#define TOD_JUMPPAD_WIND_ALIAS   "tod_jump_wind"   // sound/aliases/tod_ui.csv: 3D LOOPING on the rider's mover (tod_full_steam_wind.wav)
#define TOD_JUMPPAD_WIND_FADE    1.2     // s before the set-down the air fades out (StopLoopSound's fade is >= 1)
#define TOD_JUMPPAD_POLL         0.05    // the pad reads its deck every server frame: "as soon as you walk onto it"
#define TOD_JUMPPAD_Z_BAND       48      // standing on the deck, not passing over it
#define TOD_JUMPPAD_HOLD_MS      1500    // a landing spot stays reserved this long past its flight
#define TOD_JUMPPAD_REFUSE_LOG_MS 3000   // one REFUSE line per player per reason per this long
#define TOD_JUMPPAD_ROOF_ZONE    "roof_zone"   // the landing deck's zone (gen_tower_map.js ZONES)
#define TOD_JUMPPAD_LOG          1       // TEMPORARY — logs with dev OFF for the first playtests; zero before publish

// THE OPENING SCENE (docs/196). Seconds are measured from the launch.
#define TOD_JUMPPAD_CINE         1       // 0 = no scene: every flight is a plain free-look flight
#define TOD_JUMPPAD_CINE_EVERY   0       // 1 = the scene plays on EVERY flight (tuning only; 0 ships: "only on the first time")
// THE CAMERA PATH (the second pass, 2026-09-30; cine_cam_angles below). The first pass locked the view with a
// LerpViewAngleClamp closing late onto a mover turned by four separate RotateTo moves, and at the end dipped the view
// 32 deg down and pulled it 24 deg back up while handing control back: the user's "not super smooth ... wavers back
// and forth towards the end of jump". Now the camera is ONE path from the rider's own view, every piece eased.
// THE FIFTH PASS (2026-09-30; the user after playing the fourth: "things happen a bit too slow, so it's almost like you're
// waiting at each step ... sitting there a little bit too long waiting for the spaceships to explode ... when they explode
// you almost still see the sign but it's not even glowing, taking a little bit too long to light up"): the turn 2.25 -> 1.6 s,
// the standoff 0.8 -> 0.6 s, the ram 1.2 -> 1.1 s, the sign lights 1.0 s after the impact instead of 2.4, ~2.7 s on the lit
// title instead of ~3, the swing back 1.8 -> 1.5 s, the flight 13.8 -> 11.6 s. The same beats, every gap shorter.
#define TOD_JUMPPAD_CINE_TURN_AT    0.3  // the camera holds the rider's own view as they leave the balcony, then turns
#define TOD_JUMPPAD_CINE_TURN_SECS  1.6  // the turn's YAW onto the sign (eased) for a turn up to TURN_REF deg: it settles at 1.9 s
                                         // (2.6 in the fourth pass); a bigger turn takes proportionally longer, up to TURN_MAX
#define TOD_JUMPPAD_CINE_TURN_REF   110  // deg of yaw the turn covers in TURN_SECS (a rider who walked onto the pad facing the flight
                                         // +- 30 turns ~60-120 deg); the beats after the settle are absolute, so ...
#define TOD_JUMPPAD_CINE_TURN_MAX   2.05 // ... the longest turn (a rider facing 90 deg off the flight turns 180) still settles before
                                         // the charge and never steps past test_jumppad's 150 deg/s
#define TOD_JUMPPAD_CINE_PITCH_SECS 1.0  // the turn's PITCH leads (level with the sign by ~1.35 s), so both warships warp in
                                         // (0.8 with the 1.6 s turn stepped the camera 7.7 deg a frame from a low launch view)
                                         // on screen; a bigger tilt takes longer (PITCH_REF deg per PITCH_SECS)
#define TOD_JUMPPAD_CINE_PITCH_REF  45
#define TOD_JUMPPAD_CINE_HOLD_SECS  6.5  // on the sign from the settle (1.9 s) to the swing back (8.4 s): the standoff, the crash, the fire
                                         // and ~3.5 s on the lit title; the apex (and its dwell) rides through it (6.0 until 2026-10-01:
                                         // the user's "another 500ms before going down")
// THE CRASH (docs/196 §4, user 2026-09-29: "the skybox sign is like dimmed then there are two of the
// spaceships going at each other ... they crash into each other they do a huge explosion so you can't
// see anything and then behind is actually the tower of doom sign all lit up completely bright").
// Absolute seconds from the launch. The flyer's CLIENT plays the ships / fireball / sign
// (_tod_jump_title.csc, LOCKSTEP: its TOD_JT_RUN_SECS = IMPACT_AT - SHIPS_AT); this file sends the
// beats and owns the camera, the white-out (TodJumpCine.lua), the shake and the rumble.
#define TOD_JUMPPAD_CINE_SHIPS_AT   2.5  // the standoff breaks: both gunships charge (0.6 s of bow-to-bow standoff after the settle)
#define TOD_JUMPPAD_CINE_IMPACT_AT  3.6  // they meet nose to nose: the white flash, the fireball, boom, shake (a 1.1 s ram)
#define TOD_JUMPPAD_CINE_IGNITE_AT  3.8  // BEHIND the full white (3.66..3.91 s, TodJumpCine FLASH_IN/HOLD_MS): arms the client's REVEAL
                                         // (ignite + 0.7 s = 0.9 s after the impact, as the white burns out onto the fireball: the power
                                         // surge, the LIT SIGN CARD flickers on through the fire and holds, the glows surge, the ring
                                         // and the eyes flare); 9c's salute cue
#define TOD_JUMPPAD_CINE_QUAKE      0.42 // the impact's camera shake (Earthquake scale; the launch kick is 0.35)
#define TOD_JUMPPAD_CINE_QUAKE_SECS 1.8
#define TOD_JUMPPAD_CINE_QUAKE_R    2000 // ... its reach: the rider flies ~800 u while it rolls (160 left the shake after ~0.3 s)
#define TOD_JUMPPAD_CINE_BACK_SECS  1.5  // ONE eased move from the sign down to the landing view (it ends at 9.9 s)
#define TOD_JUMPPAD_CINE_FREE_SECS  1.0  // then the clamp opens back to free look over a camera that has stopped
// Where the sign is (docs/196 §3, MEASURED in game): YAW = -(the SSIs' sun azimuth 140 + skyRotation 40) - roll 0
// = due WEST (LOCKSTEP with docs/sky_preview/sky3d_stats.json "roll", tod_skybox.gdt skyRotation and the live
// SSIs' yaw / pitch; test_jumppad checks every one). PITCH frames the whole 65 deg gate inside the 2.35:1 bars
// (seen el -6.9..32.9, the drift ends at 34.4): the spire tip (el 34.7) under the top bar, the banners' demon faces
// above the bottom one, the text box (el 11) 2 deg below centre. -11 cut the spire at the bar (engine-mapped renders).
#define TOD_JUMPPAD_CINE_SIGN_YAW    180
#define TOD_JUMPPAD_CINE_SIGN_PITCH  ( -13 )
#define TOD_JUMPPAD_CINE_DRIFT_YAW   4     // the hold drifts a few degrees so the shot never freezes
#define TOD_JUMPPAD_CINE_DRIFT_PITCH ( -1.5 )
#define TOD_JUMPPAD_CINE_LAND_PITCH  16    // the landing view: the flight's heading, a little down the terrace (the first pass went
                                           // to 32 and back up to 8: the waver)

#namespace tod_jumppad;

function init()
{
	if ( !tod_crown_data::jumppad_enabled() )
		return;   // the road is whole (CW_CUT false): nothing to jump

	level.tod_jumppad_launches = 0;
	level.tod_jumppad_reserved = [];   // landing spot index -> GetTime() the reservation lapses

	// Both hooks go in BEFORE the first wait, so they are live before anyone
	// could possibly stand on the pad.
	level.tod_jumppad_prev_oopa_cb = level.player_out_of_playable_area_monitor_callback;
	level.player_out_of_playable_area_monitor_callback = &playable_area_cb;
	if ( !isdefined( level.player_damage_callbacks ) )
		level.player_damage_callbacks = [];
	ArrayInsert( level.player_damage_callbacks, &flight_damage_guard, 0 );

	level flag::wait_till( "initial_blackscreen_passed" );
	level.tod_jumppad_flights = [];   // op -> true while that flight is in the air (the landing pad glows for them)

	// THE MACHINE: DE's jumpsphere and its deck at one origin and yaw (DE's own assembly), dark until the power, and
	// DE's landing pad on the landing deck.
	org = tod_crown_data::jumppad_launch_org();
	ang = ( 0, tod_crown_data::jumppad_launch_yaw(), 0 );
	level.tod_jumppad_frame = spawn_prop( TOD_JUMPPAD_MODEL_FRAME, org, ang );
	level.tod_jumppad_deck = spawn_prop( TOD_JUMPPAD_MODEL_DECK_OFF, org, ang );
	level.tod_jumppad_landpad = spawn_prop( TOD_JUMPPAD_MODEL_LAND_OFF, tod_crown_data::jumppad_land_center(), ( 0, tod_crown_data::jumppad_land_yaw(), 0 ) );
	level thread power_watch();

	spots = tod_crown_data::jumppad_land_orgs();
	jp_log( "INIT rev=7 pad=de_jumpsphere cam=path sign=dull_bake+card move=lookahead+dwell pad=" + org + " yaw=" + ang[ 1 ] + " r=" + tod_crown_data::jumppad_trigger_r() + " land=" + tod_crown_data::jumppad_land_center()
	        + " spots=" + spots.size + " frame_ok=" + isdefined( level.tod_jumppad_frame ) + " deck_ok=" + isdefined( level.tod_jumppad_deck )
	        + " landpad_ok=" + isdefined( level.tod_jumppad_landpad ) + " flight=" + TOD_JUMPPAD_FLIGHT_SECS + "s cine=" + TOD_JUMPPAD_CINE_SECS
	        + "s dwell=" + TOD_JUMPPAD_CINE_DWELL + "@" + TOD_JUMPPAD_CINE_DWELL_AT + " hold=" + TOD_JUMPPAD_CINE_HOLD_SECS
	        + " apex=" + TOD_JUMPPAD_APEX + " lookahead=" + TOD_JUMPPAD_LOOKAHEAD + " scene=" + TOD_JUMPPAD_CINE + " every=" + TOD_JUMPPAD_CINE_EVERY
	        + " sign_yaw=" + TOD_JUMPPAD_CINE_SIGN_YAW + " sign_pitch=" + TOD_JUMPPAD_CINE_SIGN_PITCH
	        + " damage_cbs=" + level.player_damage_callbacks.size );
	level thread pad_watch();
}

// ---------------------------------------------------------------------------
// THE MACHINE (docs/163 s9) - DE's jumpsphere: its props, its states, its effects.
// ---------------------------------------------------------------------------
function spawn_prop( model, org, ang )
{
	m = Spawn( "script_model", org );
	if ( !isdefined( m ) )
	{
		jp_log( "FX_FAIL prop=" + model + " why=spawn" );
		return undefined;
	}
	m SetModel( model );
	m.angles = ang;
	return m;
}

// THE LEVER IS THE POWER (2026-09-25): the pad refuses until then (refuse_reason), and now it LOOKS dead until then
// too - DE's plain deck, lights dark - and wakes with DE's crackle and its blue lights the moment the power comes on.
function power_watch()
{
	level endon( "end_game" );
	while ( !level flag::exists( "power_on" ) )
		wait 0.5;
	level flag::wait_till( "power_on" );
	if ( isdefined( level.tod_jumppad_deck ) )
		level.tod_jumppad_deck SetModel( TOD_JUMPPAD_MODEL_DECK_ON );
	if ( isdefined( level.tod_jumppad_landpad ) )
		level.tod_jumppad_landpad SetModel( TOD_JUMPPAD_MODEL_LAND_ON );
	tod_perk_scatter::play_sound_at_origin( tod_crown_data::jumppad_launch_org() + ( 0, 0, 40 ), TOD_JUMPPAD_SND_CHARGE, 3 );
	jp_log( "STATE pad=ready deck=" + ( ( isdefined( level.tod_jumppad_deck ) ) ? level.tod_jumppad_deck.model : "NONE" )
	        + " landpad=" + ( ( isdefined( level.tod_jumppad_landpad ) ) ? level.tod_jumppad_landpad.model : "NONE" ) + " round=" + level.round_number );
}

// A throwaway FX host (the teleporter's proven fx_burst, oriented: DE's effects place their arcs relative to the
// machine): spawn, give the clients two frames to know the host, play, hold, delete. NO endon - a thread killed
// mid-wait would orphan the host - and ALWAYS THREADED: it waits out the effect's life (the Battle Arena's 6.6 s
// teleport was three of these called inline, 2026-10-03).
function fx_burst( fx, origin, angles, secs )
{
	h = Spawn( "script_model", origin );
	if ( !isdefined( h ) )
	{
		jp_log( "FX_FAIL fx=" + fx + " why=host_spawn at=" + origin );
		return;
	}
	h SetModel( "tag_origin" );
	h.angles = angles;
	WAIT_SERVER_FRAME;
	WAIT_SERVER_FRAME;
	if ( !isdefined( h ) )
		return;
	PlayFXOnTag( fx, h, "tag_origin" );
	wait secs;
	if ( isdefined( h ) )
		h Delete();
}

// DE's electric trail on the rider for the climb (finite, ~1.2 s): on the flight's own mover, so it rides the arc and
// dies with it. self = the mover.
function trail_fx()
{
	self endon( "death" );
	WAIT_SERVER_FRAME;
	WAIT_SERVER_FRAME;
	if ( isdefined( self ) )
		PlayFXOnTag( TOD_JUMPPAD_FX_TRAIL, self, "tag_origin" );
}

// The landing pad lights up for whoever is coming down: DE's glow, re-pulsed while any flight is in the air (a beacon
// the rider sees from the top of the arc). One runner at a time.
function land_glow()
{
	level endon( "end_game" );
	if ( IS_TRUE( level.tod_jumppad_glowing ) )
		return;
	level.tod_jumppad_glowing = true;
	org = tod_crown_data::jumppad_land_center();
	ang = ( 0, tod_crown_data::jumppad_land_yaw(), 0 );
	while ( isdefined( level.tod_jumppad_flights ) && level.tod_jumppad_flights.size > 0 )
	{
		level thread fx_burst( TOD_JUMPPAD_FX_GLOW, org, ang, TOD_JUMPPAD_FX_GLOW_SECS );
		wait TOD_JUMPPAD_FX_GLOW_EVERY;
	}
	level.tod_jumppad_glowing = undefined;
}

// ---------------------------------------------------------------------------
// THE PAD — no trigger entity: every living player's origin is tested against
// the deck circle each server frame (four players, four distance tests).
// ---------------------------------------------------------------------------
function pad_watch()
{
	level endon( "end_game" );
	org = tod_crown_data::jumppad_launch_org();
	r = tod_crown_data::jumppad_trigger_r();
	r2 = r * r;
	for ( ;; )
	{
		wait TOD_JUMPPAD_POLL;
		players = GetPlayers();
		for ( i = 0; i < players.size; i++ )
		{
			p = players[ i ];
			if ( !isdefined( p ) || !isplayer( p ) || IS_TRUE( p.tod_jumppad_flying ) )
				continue;
			if ( Distance2DSquared( p.origin, org ) > r2 )
				continue;
			if ( abs( p.origin[ 2 ] - org[ 2 ] ) > TOD_JUMPPAD_Z_BAND )
				continue;
			why = p refuse_reason();
			if ( isdefined( why ) )
			{
				p refuse_log( why );
				continue;
			}
			p thread launch();
		}
	}
}

// -> undefined when this player may fly now, else why not. self = player.
function refuse_reason()
{
	if ( !isalive( self ) )
		return "dead";
	// THE LEVER IS THE POWER (2026-09-25): the pad is dead until the grid is on
	if ( !( level flag::exists( "power_on" ) && level flag::get( "power_on" ) ) )
		return "no_power";
	if ( isdefined( self.sessionstate ) && self.sessionstate != "playing" )
		return "not_playing";
	// A crawler never flies: its revive trigger rides the player and a
	// teammate reviving it would be left kneeling at an empty pad.
	if ( self laststand::player_is_in_laststand() )
		return "downed";
	// A frozen world (upgrade cards, a solo altar buy) moves nothing; the pad
	// fires the moment it lifts if the player is still standing on it.
	if ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( self.tod_menu_frozen ) )
		return "world_paused";
	if ( isdefined( self GetLinkedEnt() ) )
		return "already_linked";
	if ( !( self IsOnGround() ) )
		return "airborne";   // jumped onto the pad: fires on touch-down, the next frame it is grounded
	return undefined;
}

function refuse_log( why )   // self = player
{
	if ( why == "airborne" )
		return;   // a hop onto the pad is not news
	now = GetTime();
	if ( isdefined( self.tod_jumppad_refuse_why ) && self.tod_jumppad_refuse_why == why
	     && isdefined( self.tod_jumppad_refuse_ms ) && now - self.tod_jumppad_refuse_ms < TOD_JUMPPAD_REFUSE_LOG_MS )
		return;
	self.tod_jumppad_refuse_why = why;
	self.tod_jumppad_refuse_ms = now;
	jp_log( "REFUSE player=" + self GetEntityNumber() + " why=" + why + " at=" + self.origin );
}

// ---------------------------------------------------------------------------
// THE FLIGHT. self = player.
// ---------------------------------------------------------------------------
function launch()
{
	self endon( "disconnect" );
	self endon( "death" );

	self.tod_jumppad_flying = true;   // FIRST: pad_watch skips a flyer from this line on
	level.tod_jumppad_launches++;
	op = level.tod_jumppad_launches;
	t0 = GetTime();
	src = self.origin;
	pad = tod_crown_data::jumppad_launch_org();

	// THE OPENING SCENE: a player's first flight is the long, directed one.
	cine = self cine_wanted();
	secs = TOD_JUMPPAD_FLIGHT_SECS;
	if ( cine )
		secs = TOD_JUMPPAD_CINE_SECS;

	k = pick_landing();
	spots = tod_crown_data::jumppad_land_orgs();
	dst = spots[ k ];
	level.tod_jumppad_reserved[ k ] = t0 + int( secs * 1000 ) + TOD_JUMPPAD_HOLD_MS;

	// The landing deck's zone must be live before anyone stands on it (a
	// DISABLED zone is the Samantha-laugh instakill). The zone script enables
	// it when the Fall gate is bought; this is the belt to that brace.
	zone_on = ensure_landing_zone();

	mover = Spawn( "script_model", src );
	if ( !isdefined( mover ) )
	{
		// entity pool full: stay on the pad, nothing spent; the next frame retries
		self.tod_jumppad_flying = undefined;
		jp_log( "ABORT op=" + op + " player=" + self GetEntityNumber() + " why=mover_spawn_failed" );
		return;
	}
	mover SetModel( "tag_origin" );
	yaw = VectorToAngles( dst - src );
	mover.angles = ( 0, yaw[ 1 ], 0 );
	// THE SCENE'S CAMERA: the mover takes the rider's own view BEFORE the link, so the lock closes on exactly what
	// they were looking at; from then on one path moves it (cine_cam_angles), stepped below with the arc.
	cam = undefined;
	if ( cine )
	{
		cam = cine_cam_plan( self GetPlayerAngles(), yaw[ 1 ] );
		mover.angles = cine_cam_angles( cam, 0 );
	}
	self.tod_jumppad_cam = cam;
	self.tod_jumppad_cam_cut = undefined;

	self zm_utility::increment_ignoreme();
	self.tod_jumppad_ignore = true;
	self.tod_jumppad_mover = mover;
	level thread flight_guard( self, mover, op );

	self SetStance( "stand" );
	if ( cine )
		self PlayerLinkToDelta( mover, "tag_origin", 1, 0, 0, 0, 0 );      // the scene: locked on the camera path
	else
		self PlayerLinkToDelta( mover, "tag_origin", 1, 180, 180, 75, 75 );

	// THE LAUNCH (DE's flinger): the machine crackles and fires its burst at the pad - the rider hears it fall away
	// behind them - the fling whooshes off WITH them (on the mover) under DE's electric trail, and a kick. The landing
	// pad starts glowing for the inbound rider.
	tod_perk_scatter::play_sound_at_origin( pad + ( 0, 0, 40 ), TOD_JUMPPAD_SND_CHARGE, 3 );
	level thread fx_burst( TOD_JUMPPAD_FX_LAUNCH, pad, ( 0, tod_crown_data::jumppad_launch_yaw(), 0 ), TOD_JUMPPAD_FX_LAUNCH_SECS );
	mover PlaySound( TOD_JUMPPAD_SND_LAUNCH );
	mover thread trail_fx();
	level.tod_jumppad_flights[ op ] = true;
	level thread land_glow();
	Earthquake( 0.35, 0.6, pad, 360 );
	self PlayRumbleOnEntity( "damage_heavy" );
	// THE AIR: a 3D wind loop that rides the rider's own mover (a teammate
	// launched beside you hears yours; nobody on the ground does).
	mover PlayLoopSound( TOD_JUMPPAD_WIND_ALIAS, 1 );

	jp_log( "LAUNCH op=" + op + " player=" + self GetEntityNumber() + " src=" + src + " dst=" + dst + " spot=" + k
	        + " secs=" + secs + " cine=" + cine + " round=" + level.round_number + " roof_zone_on=" + zone_on
	        + " fall_sealed=" + IS_TRUE( level.tod_fall_sealed ) );
	if ( cine )
		self thread cine_run( mover, op );

	// THE ARC: straight line between the two feet positions plus a parabola
	// peaking TOD_JUMPPAD_APEX above it at the midpoint — the SAME shape
	// test_jumppad sweeps — walked on the hang clock. Exact at both ends.
	n = int( secs / TOD_JUMPPAD_STEP + 0.5 );
	wind_off = n - int( TOD_JUMPPAD_WIND_FADE / TOD_JUMPPAD_STEP + 0.5 );
	d = dst - src;
	track_err = 0;
	for ( i = 1; i <= n; i++ )
	{
		if ( !isdefined( mover ) )
			break;   // the guard cleaned up under us
		// where the arc says the mover should be NOW (frame i - 1): the tracking error of the lookahead, logged a few times
		if ( i > 1 && ( ( i - 1 ) % 40 == 0 || i == n ) )
		{
			err = Distance( mover.origin, arc_point( src, d, i - 1, n, cine ) );
			if ( err > track_err )
				track_err = err;
			jp_log( "TRACK op=" + op + " frame=" + ( i - 1 ) + "/" + n + " err=" + err );
		}
		// THE TRAJECTORY FIX: aim TOD_JUMPPAD_LOOKAHEAD frames ahead over as many frames (see the define); the last frames
		// aim at the arc's end over what is left, so the mover is on the spot when the loop ends
		j = i + TOD_JUMPPAD_LOOKAHEAD - 1;
		if ( j > n )
			j = n;
		secs_move = ( j - i + 1 ) * TOD_JUMPPAD_STEP;
		mover MoveTo( arc_point( src, d, j, n, cine ), secs_move );
		// the camera path, the same lookahead alongside the arc (until it has stopped, or a menu cut the scene)
		if ( isdefined( cam ) && !IS_TRUE( self.tod_jumppad_cam_cut ) && ( i - 1 ) * TOD_JUMPPAD_STEP < cam.still_at )
			mover RotateTo( cine_cam_step( mover.angles, cine_cam_angles( cam, j * TOD_JUMPPAD_STEP ) ), secs_move );
		if ( i == wind_off )
			mover StopLoopSound( 1 );
		wait TOD_JUMPPAD_STEP;
	}

	// SET DOWN: exactly on the spot, standing, no momentum carried.
	self Unlink();
	self SetOrigin( dst );
	self SetVelocity( ( 0, 0, 0 ) );
	if ( isdefined( mover ) )
	{
		mover StopLoopSound( 1 );
		mover Delete();
	}
	self finish();
	self notify( "tod_jumppad_landed" );
	level.tod_jumppad_flights[ op ] = undefined;

	// THE ARRIVAL (DE's landing smash): dust bursting off the landing pad round the feet, the thud, a kick.
	level thread fx_burst( TOD_JUMPPAD_FX_DUST, dst, ( 0, yaw[ 1 ], 0 ), TOD_JUMPPAD_FX_DUST_SECS );
	tod_perk_scatter::play_sound_at_origin( dst + ( 0, 0, 16 ), TOD_JUMPPAD_SND_LAND, 3 );
	Earthquake( 0.3, 0.5, dst, 300 );
	self PlayRumbleOnEntity( "damage_heavy" );

	// A ride moved a player thousands of units: the same two signals a
	// teleporter ride sends (_tod_teleport::do_teleport) — tod_boss_stuck_watch
	// re-bases its no-progress accumulator on the stamp, and _tod_stray runs
	// hot so the horde meets the party instead of trailing it.
	level.tod_tp_stamp = ( ( isdefined( level.tod_tp_stamp ) ) ? level.tod_tp_stamp + 1 : 1 );
	level notify( "tod_stray_pump" );

	zn = zm_zonemgr::get_zone_from_position( self.origin + ( 0, 0, 32 ), false );
	jp_log( "LAND op=" + op + " player=" + self GetEntityNumber() + " at=" + self.origin + " spot=" + k
	        + " flight_ms=" + ( GetTime() - t0 ) + " cine=" + cine + " zone=" + ( ( isdefined( zn ) ) ? zn : "NONE" )
	        + " track_err_max=" + track_err );
}

// -> the arc's point at frame i of n: the straight line between the feet plus the parabola, walked on the hang
// clock (frame n is exactly the landing spot); a first flight (cine) walks it with THE DWELL at the top.
function arc_point( src, d, i, n, cine )
{
	u = 1.0;
	if ( i < n )
	{
		if ( IS_TRUE( cine ) )
			u = hang_u( cine_arc_frac( i * TOD_JUMPPAD_STEP ) );
		else
			u = hang_u( i / ( n * 1.0 ) );
	}
	lift = 4.0 * TOD_JUMPPAD_APEX * u * ( 1.0 - u );
	return src + VectorScale( d, u ) + ( 0, 0, lift );
}

// -> the share of the arc's hang clock walked t seconds into a FIRST flight: the arc's own clock is CINE_SECS - DWELL
// long, and CINE_DWELL seconds are slipped in round the apex as a raised-cosine slow-down over DWELL_SPAN (the clock's
// pace dips to 1 - 2 DWELL / SPAN at the middle and is whole again at both ends: no stop, no kink). sin takes DEGREES.
function cine_arc_frac( t )
{
	x = t - ( TOD_JUMPPAD_CINE_DWELL_AT - TOD_JUMPPAD_CINE_DWELL_SPAN * 0.5 );
	if ( x > TOD_JUMPPAD_CINE_DWELL_SPAN )
		x = TOD_JUMPPAD_CINE_DWELL_SPAN;
	if ( x > 0 )
		t = t - TOD_JUMPPAD_CINE_DWELL * ( x / TOD_JUMPPAD_CINE_DWELL_SPAN - sin( 360.0 * x / TOD_JUMPPAD_CINE_DWELL_SPAN ) / TOD_JUMPPAD_TWO_PI );
	return t / ( TOD_JUMPPAD_CINE_SECS - TOD_JUMPPAD_CINE_DWELL );
}

// -> u in [0,1] along the arc for t in [0,1] of the flight: THE HANG CLOCK
// (the header of the defines above). sin/cos take DEGREES in GSC: 2 pi t rad = 360 t deg.
function hang_u( t )
{
	a = 360.0 * t;
	u = t + TOD_JUMPPAD_WARP_A * sin( a ) / TOD_JUMPPAD_TWO_PI
	      - TOD_JUMPPAD_WARP_B * ( cos( a ) - 1.0 ) / TOD_JUMPPAD_TWO_PI
	      + TOD_JUMPPAD_WARP_C * sin( 2.0 * a ) / ( 2.0 * TOD_JUMPPAD_TWO_PI )
	      - TOD_JUMPPAD_WARP_D * ( cos( 2.0 * a ) - 1.0 ) / ( 2.0 * TOD_JUMPPAD_TWO_PI )
	      + TOD_JUMPPAD_WARP_L * ( t - t * t );
	if ( u < 0 )
		return 0;
	if ( u > 1 )
		return 1;
	return u;
}

// Clean-up for a flight that does not reach its landing (death, disconnect).
// Level-threaded so it survives the flight thread's own endons.
function flight_guard( player, mover, op )
{
	msg = player util::waittill_any_return( "tod_jumppad_landed", "disconnect", "death" );
	if ( isdefined( msg ) && msg == "tod_jumppad_landed" )
		return;
	level.tod_jumppad_flights[ op ] = undefined;   // nobody is coming down for this one: the landing pad's glow stops
	if ( isdefined( mover ) )
	{
		mover StopLoopSound( 1 );
		mover Delete();
	}
	if ( isdefined( player ) && isplayer( player ) )
	{
		player Unlink();
		player finish();
	}
	jp_log( "ABORT op=" + op + " why=" + ( ( isdefined( msg ) ) ? msg : "unknown" ) );
}

// Release everything launch() took. Idempotent. self = player.
function finish()
{
	self cine_end( 0, "flight_end" );   // no-op unless a scene is still up (death / disconnect mid-scene)
	if ( IS_TRUE( self.tod_jumppad_ignore ) )
	{
		self.tod_jumppad_ignore = undefined;
		self zm_utility::decrement_ignoreme();
	}
	self.tod_jumppad_mover = undefined;
	self.tod_jumppad_cam = undefined;
	self.tod_jumppad_cam_cut = undefined;
	self.tod_jumppad_flying = undefined;
}

// ---------------------------------------------------------------------------
// THE OPENING SCENE (docs/196). self = player throughout.
// ---------------------------------------------------------------------------

// -> true when this flight should be the directed one.
function cine_wanted()
{
	if ( !TOD_JUMPPAD_CINE )
		return false;
	if ( IS_TRUE( self.tod_jumppad_cine_seen ) && !TOD_JUMPPAD_CINE_EVERY )
		return false;
	// the pad refuses a paused world already; a scene must never start under a menu
	if ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( self.tod_menu_frozen ) )
		return false;
	return true;
}

function cine_run( mover, op )
{
	self endon( "disconnect" );
	self endon( "death" );

	self cine_begin( op );
	cam = self.tod_jumppad_cam;
	settle = TOD_JUMPPAD_CINE_TURN_AT + TOD_JUMPPAD_CINE_TURN_SECS;
	cine_log( op, "CAM view=(" + cam.p0 + ", " + cam.y0 + ") sign=(" + cam.sp + ", " + cam.sy + ") land=(" + cam.lp + ", " + cam.ly
	          + ") turn_secs=" + cam.ty + " pitch_secs=" + cam.pt + " still_at=" + cam.still_at );

	// 1. THE TURN - the camera (locked on the rider's own view since the launch) eases round to the dark sign, a right
	// turn for a rider facing down the flight; its pitch leads, so the magenta gunship warping in high on the left is
	// in the shot. The flight loop in launch() steps it every server frame; nothing here rotates anything.
	if ( !self cine_wait( TOD_JUMPPAD_CINE_TURN_AT, op ) )
		return;
	cine_log( op, "TURN from=" + mover.angles + " to=(" + cam.sp + ", " + cam.sy + ") player_angles=" + self GetPlayerAngles()
	          + " z=" + mover.origin[ 2 ] );

	// 2. THE STANDOFF - the camera settles on the DIMMED sign; two gunships hang in front of it, facing each other
	// (the client has had them there since the launch, out of sight behind the turn, so no FOV ever sees one pop in).
	// The air falls quiet so their engines carry the shot; the wind comes back for the dive.
	if ( !self cine_wait( settle - TOD_JUMPPAD_CINE_TURN_AT, op ) )
		return;
	mover StopLoopSound( 1 );

	// 3. THE CHARGE - both engines flare and the ships ram each other.
	if ( !self cine_wait( TOD_JUMPPAD_CINE_SHIPS_AT - settle, op ) )
		return;
	self cine_beat( op, "tod_jump_title_ships", "SHIPS", mover );

	// 4. THE IMPACT - nose to nose in front of the title: the screen flashes white
	// (a quarter second of nothing), then the fireball fills the frame and burns
	// for seconds while the shot shakes (the shake's reach keeps the rider inside it).
	if ( !self cine_wait( TOD_JUMPPAD_CINE_IMPACT_AT - TOD_JUMPPAD_CINE_SHIPS_AT, op ) )
		return;
	self LuiNotifyEvent( &"tod_jump_cine", 1, 2 );
	Earthquake( TOD_JUMPPAD_CINE_QUAKE, TOD_JUMPPAD_CINE_QUAKE_SECS, mover.origin, TOD_JUMPPAD_CINE_QUAKE_R );
	self PlayRumbleOnEntity( "damage_heavy" );
	self cine_beat( op, "tod_jump_title_impact", "IMPACT", mover );

	// 5. THE IGNITION - behind the full white: the beat arms the client's reveal (ignite + 0.7 s,
	// as the fire thins: the lit sign card flickers on over the dull bake, its power surge is
	// heard then, not under the boom). The scene counts as seen from here; a scene cut after
	// this beat still lights the client's sign at once.
	if ( !self cine_wait( TOD_JUMPPAD_CINE_IGNITE_AT - TOD_JUMPPAD_CINE_IMPACT_AT, op ) )
		return;
	self cine_beat( op, "tod_jump_title_ignite", "IGNITE", mover );
	self cine_reveal( op, mover );

	// 6. THE HOLD through the fire onto the blazing title (session 9c's fighter wing
	// salutes it).
	if ( !self cine_wait( settle + TOD_JUMPPAD_CINE_HOLD_SECS - TOD_JUMPPAD_CINE_IGNITE_AT, op ) )
		return;

	// 7. THE RETURN - ONE eased move from the sign down to the landing view (the flight's heading, LAND_PITCH down);
	// the air rushes back as the dive starts. The client lets the smoke and the blaze fade as the sign leaves the frame.
	self cine_title_end();
	mover PlayLoopSound( TOD_JUMPPAD_WIND_ALIAS, 1 );
	cine_log( op, "RETURN from=" + mover.angles + " to=(" + cam.lp + ", " + cam.ly + ") at=" + mover.origin );
	if ( !self cine_wait( TOD_JUMPPAD_CINE_BACK_SECS, op ) )
		return;

	// 8. FREE - the camera has stopped on the landing view: the clamp opens, the bars and the HUD come back, the gun
	// comes up. Nothing turns the camera after this (the first pass pitched it back up here, under the player's own
	// hand: the waver).
	self LerpViewAngleClamp( TOD_JUMPPAD_CINE_FREE_SECS, TOD_JUMPPAD_CINE_FREE_SECS * 0.3, TOD_JUMPPAD_CINE_FREE_SECS * 0.5, 180, 180, 75, 75 );
	left = TOD_JUMPPAD_CINE_SECS - settle - TOD_JUMPPAD_CINE_HOLD_SECS - TOD_JUMPPAD_CINE_BACK_SECS;
	cine_log( op, "FREE left=" + left + " angles=" + mover.angles + " planned=(" + cam.lp + ", " + cam.ly + ") player_angles="
	          + self GetPlayerAngles() );
	self cine_end( op, "done" );
}

// ---------------------------------------------------------------------------
// THE CAMERA PATH (the second pass, 2026-09-30; the user after the first real
// run: "not super smooth. The player wavers back and forth towards the end of
// jump"). ONE path, a pure function of the flight clock, stepped with the arc
// every server frame (launch()):
//   0 .. TURN_AT             the rider's own view, held (the lock closed on it)
//   TURN_AT .. +pt           the pitch eases onto the sign's (it leads)
//   TURN_AT .. settle        the yaw eases onto the sign's bearing, the short way
//   settle .. swing          the hold's slow drift
//   swing .. swing + BACK    ONE eased move to the landing view
//   after                    still: control comes back to a stopped camera
// Every piece is a smoothstep, so it never jerks and never turns back on
// itself. tools/test_jumppad.js and tools/jump_title/test_jump_title.js RUN
// these functions (tools/sky_ships/gsc_eval.js), never a copy.
// ---------------------------------------------------------------------------

// -> the plan for a first flight: the rider's view (GetPlayerAngles at the launch) and the flight's heading. The hold,
// the swing and the still point are ABSOLUTE (the beats are); only the turn's own ease (c.ty, c.pt) fits the rider.
function cine_cam_plan( view, flight_yaw )
{
	c = SpawnStruct();
	c.p0 = view[ 0 ];
	c.y0 = view[ 1 ];
	c.sp = TOD_JUMPPAD_CINE_SIGN_PITCH;
	c.sy = c.y0 + AngleClamp180( TOD_JUMPPAD_CINE_SIGN_YAW - c.y0 );
	tilt = abs( c.sp - c.p0 ) / TOD_JUMPPAD_CINE_PITCH_REF;
	if ( tilt < 1 )
		tilt = 1;
	c.pt = TOD_JUMPPAD_CINE_PITCH_SECS * tilt;
	// the yaw's ease scales with the turn (fifth pass): a short turn takes TURN_SECS, a big one up to TURN_MAX
	turn = abs( c.sy - c.y0 ) / TOD_JUMPPAD_CINE_TURN_REF;
	if ( turn < 1 )
		turn = 1;
	c.ty = TOD_JUMPPAD_CINE_TURN_SECS * turn;
	if ( c.ty > TOD_JUMPPAD_CINE_TURN_MAX )
		c.ty = TOD_JUMPPAD_CINE_TURN_MAX;
	if ( c.pt > c.ty )
		c.pt = c.ty;
	c.hp = c.sp + TOD_JUMPPAD_CINE_DRIFT_PITCH;
	c.hy = c.sy + TOD_JUMPPAD_CINE_DRIFT_YAW;
	c.lp = TOD_JUMPPAD_CINE_LAND_PITCH;
	c.ly = c.hy + AngleClamp180( flight_yaw - c.hy );
	c.still_at = TOD_JUMPPAD_CINE_TURN_AT + TOD_JUMPPAD_CINE_TURN_SECS + TOD_JUMPPAD_CINE_HOLD_SECS + TOD_JUMPPAD_CINE_BACK_SECS;
	return c;
}

// -> the camera's angles t seconds into the flight (unwrapped: yaw may run past +-180).
function cine_cam_angles( c, t )
{
	settle = TOD_JUMPPAD_CINE_TURN_AT + TOD_JUMPPAD_CINE_TURN_SECS;
	swing = settle + TOD_JUMPPAD_CINE_HOLD_SECS;
	if ( t < swing )
	{
		fp = cine_ease( ( t - TOD_JUMPPAD_CINE_TURN_AT ) / c.pt );
		fy = cine_ease( ( t - TOD_JUMPPAD_CINE_TURN_AT ) / c.ty );
		fh = cine_ease( ( t - settle ) / TOD_JUMPPAD_CINE_HOLD_SECS );
		return ( c.p0 + ( c.sp - c.p0 ) * fp + ( c.hp - c.sp ) * fh, c.y0 + ( c.sy - c.y0 ) * fy + ( c.hy - c.sy ) * fh, 0 );
	}
	f = cine_ease( ( t - swing ) / TOD_JUMPPAD_CINE_BACK_SECS );
	return ( c.hp + ( c.lp - c.hp ) * f, c.hy + ( c.ly - c.hy ) * f, 0 );
}

// -> `want` expressed next to `now` (each angle within 180 of the mover's own), so a RotateTo always takes the short
// way whatever range the engine keeps the mover's angles in.
function cine_cam_step( now, want )
{
	return ( now[ 0 ] + AngleClamp180( want[ 0 ] - now[ 0 ] ), now[ 1 ] + AngleClamp180( want[ 1 ] - now[ 1 ] ), 0 );
}

// smoothstep: 0 -> 1 with no speed at either end.
function cine_ease( x )
{
	if ( x <= 0 )
		return 0;
	if ( x >= 1 )
		return 1;
	return x * x * ( 3 - 2 * x );
}

function cine_begin( op )
{
	self.tod_jumppad_cine = op;
	self HideViewModel();
	// The gun goes down for the shot — unless a menu already holds it (then the
	// menu's unfreeze owns the hand-back, never this scene).
	if ( !IS_TRUE( self.tod_menu_frozen ) )
	{
		self DisableWeapons();
		self DisableOffhandWeapons();
		self.tod_jumppad_cine_arms = true;
	}
	self LuiNotifyEvent( &"tod_jump_cine", 1, 1 );
	// the flyer's client dims the sign and parks the two gunships in their standoff now,
	// while the camera still faces the tower (_tod_jump_title.csc)
	self.tod_jumppad_cine_title = true;
	self util::clientNotify( "tod_jump_title_start" );
	cine_log( op, "START player=" + self GetEntityNumber() + " angles=" + self GetPlayerAngles() + " arms=" + IS_TRUE( self.tod_jumppad_cine_arms ) );
}

// One beat of THE CRASH, to the flyer's client only (util::clientNotify on a player).
function cine_beat( op, note, tag, mover )
{
	self util::clientNotify( note );
	cine_log( op, tag + " player=" + self GetEntityNumber() + " at=" + mover.origin + " angles=" + self GetPlayerAngles() );
}

// THE CRASH's last beat, exactly once per scene: at the swing back on a full scene
// (the client fades the smoke and the blaze as the sign leaves the frame), or at
// once from cine_end when the scene is cut short (the client drops everything).
function cine_title_end()
{
	if ( !IS_TRUE( self.tod_jumppad_cine_title ) )
		return;
	self.tod_jumppad_cine_title = undefined;
	self util::clientNotify( "tod_jump_title_end" );
}

function cine_reveal( op, mover )
{
	// NO clientNotify here: the beat (tod_jump_title_ignite, which session 9c's salute also
	// hears) went out this frame, and util::clientNotify is a per-player STATE (stock
	// setClientSysState "levelNotify"): a second one in the same frame would overwrite it.
	self.tod_jumppad_cine_seen = true;
	first = !IS_TRUE( level.tod_jump_title );
	if ( first )
	{
		level.tod_jump_title = true;
		level notify( "tod_jump_title" );   // _tod_atmosphere's fallback cue (the band normally started on the balcony)
	}
	cine_log( op, "REVEAL player=" + self GetEntityNumber() + " music_cue=" + first + " at=" + mover.origin + " angles=" + self GetPlayerAngles() );
}

// Wait `secs` in server frames; -> false (the scene torn down) if a card deal or
// any menu freeze takes the screen, or the flight is already over.
function cine_wait( secs, op )
{
	n = int( secs / 0.05 + 0.5 );
	for ( i = 0; i < n; i++ )
	{
		if ( !isdefined( self.tod_jumppad_cine ) )
			return false;
		if ( !isdefined( self.tod_jumppad_mover ) )
		{
			self cine_end( op, "flight_over" );
			return false;
		}
		if ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( self.tod_menu_frozen ) )
		{
			// the menu owns the screen now: open the clamp at once, drop the scene
			if ( isdefined( self GetLinkedEnt() ) )
				self LerpViewAngleClamp( 0.3, 0.1, 0.1, 180, 180, 75, 75 );
			self cine_end( op, "world_pause" );
			return false;
		}
		wait 0.05;
	}
	return true;
}

// Idempotent: every exit path lands here (done, a card deal, the flight ending
// under the scene, death, disconnect via finish()).
function cine_end( op, why )
{
	if ( !isdefined( self.tod_jumppad_cine ) )
		return;
	scene = self.tod_jumppad_cine;
	self.tod_jumppad_cine = undefined;
	// cut short (a card deal, the flight ending under it): the camera path stops where it is
	if ( why != "done" )
		self.tod_jumppad_cam_cut = true;
	if ( why != "done" && isdefined( self.tod_jumppad_mover ) )
		self.tod_jumppad_mover RotateTo( self.tod_jumppad_mover.angles, 0.05 );
	self cine_title_end();   // cut short: the client drops whatever of THE CRASH is still up
	self ShowViewModel();
	if ( IS_TRUE( self.tod_jumppad_cine_arms ) )
	{
		self.tod_jumppad_cine_arms = undefined;
		if ( !IS_TRUE( self.tod_menu_frozen ) )
		{
			self EnableWeapons();
			self EnableOffhandWeapons();
		}
	}
	self LuiNotifyEvent( &"tod_jump_cine", 1, 0 );
	cine_log( scene, "END why=" + why + " seen=" + IS_TRUE( self.tod_jumppad_cine_seen ) + " menu_frozen=" + IS_TRUE( self.tod_menu_frozen ) );
}

function cine_log( op, msg )
{
	jp_log( "CINE_" + msg + " op=" + op );
}

// -> the landing spot index: among spots nobody is flying to, the one farthest
// from every living player (so nobody is set down inside a teammate); if all
// four are claimed, the one whose claim lapses first.
function pick_landing()
{
	spots = tod_crown_data::jumppad_land_orgs();
	now = GetTime();
	players = GetPlayers();
	best = -1;
	best_d = -1;
	for ( k = 0; k < spots.size; k++ )
	{
		if ( isdefined( level.tod_jumppad_reserved[ k ] ) && level.tod_jumppad_reserved[ k ] > now )
			continue;
		d = 1000000000;
		for ( i = 0; i < players.size; i++ )
		{
			p = players[ i ];
			if ( !isdefined( p ) || !isalive( p ) || IS_TRUE( p.tod_jumppad_flying ) )
				continue;
			dd = Distance2DSquared( p.origin, spots[ k ] );
			if ( dd < d )
				d = dd;
		}
		if ( d > best_d )
		{
			best = k;
			best_d = d;
		}
	}
	if ( best >= 0 )
		return best;
	best = 0;
	for ( k = 1; k < spots.size; k++ )
	{
		if ( level.tod_jumppad_reserved[ k ] < level.tod_jumppad_reserved[ best ] )
			best = k;
	}
	return best;
}

// -> true when the landing deck's zone is enabled (enabling it if not).
function ensure_landing_zone()
{
	if ( !isdefined( level.zones ) || !isdefined( level.zones[ TOD_JUMPPAD_ROOF_ZONE ] ) )
		return false;
	if ( !IS_TRUE( level.zones[ TOD_JUMPPAD_ROOF_ZONE ].is_enabled ) )
	{
		zm_zonemgr::enable_zone( TOD_JUMPPAD_ROOF_ZONE );
		jp_log( "ZONE " + TOD_JUMPPAD_ROOF_ZONE + " was disabled at a launch — enabled it" );
	}
	return true;
}

// ---------------------------------------------------------------------------
// THE HOOKS (installed by init, see the header).
// ---------------------------------------------------------------------------

// Stock's out-of-playable-area callback: TRUE = punish, FALSE = spare.
// self = player.
function playable_area_cb()
{
	if ( IS_TRUE( self.tod_jumppad_flying ) )
		return false;
	if ( isdefined( level.tod_jumppad_prev_oopa_cb ) )
		return self [[ level.tod_jumppad_prev_oopa_cb ]]();
	return true;
}

// FIRST in stock's player damage chain: 0 for a flyer, -1 (untouched, let the
// rest of the chain run) for everyone else. self = the damaged player.
function flight_damage_guard( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, psOffsetTime )
{
	if ( IS_TRUE( self.tod_jumppad_flying ) )
		return 0;
	return -1;
}

// The proven PrintLn pattern (CLAUDE.md dev-diagnostics): assemble outside
// the developer block, print inside it.
function jp_log( msg )
{
	if ( !TOD_JUMPPAD_LOG && !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_JUMPPAD] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
