// =============================================================================
// _tod_sky_ships.csc - THE SKY FLEET (docs/192). v3 (user 2026-09-29): "they don't have any propelling system ... I
// can't see any flames coming out of the back of the jets or the spaceships or kind of like some time warp black hole
// pulses ... some of the spaceships should come through like a wormhole ... fighter jets probably just need fire and
// flames and exhaust"; "flying asteroids going around space ... more subtle than the spaceships ... higher up ... still
// visible, so players can see the movement ... and also shooting stars".
//
// CLIENT ONLY, like Treyarch's Swarm (scripts/mp/killstreaks/_missile_swarm.csc): every player's own game spawns,
// flies and deletes everything here with client entities: ZERO server entities, zero network traffic. Scenery only.
//
// ONE FLIGHT (v2): a straight line through a GENERATED pass lane (_tod_sky_lanes.csc: the whole ship clears every
// brush), extended far beyond the sealed sky box both ways. The ship first appears FAR away (spawn_px pixels long,
// low over the horizon, preferably where the player is not looking), glides in, passes the tower weaving / banking /
// swaying, climbs away and shrinks into the distance.
// THE SCALED STAND-IN (v2): nothing draws outside the sealed box (+-12,032), so a ship beyond it is drawn at the SAME
// BEARING, closer and smaller (distance x k, SetScale k); a stand-in touching tod_sky_lanes::blockers() hides that tick.
//
// v3:
// REAL TIME. A client `wait` is not real time (61, 2026-09-29: frame-counted, 2.7x fast at 165 fps on the user's PC):
//   every flight advances by the GetRealTime delta and every schedule uses waitrealtime, so every frame rate flies the
//   same. The per-tick MoveTo still spans 1.25 ticks of the script clock `wait` runs on, so motion stays continuous.
// THE FLAMES. Every nozzle is a TAG on the model (tag_eng_<i>, turned to face aft), so a flame played on it sits exactly
//   on the nozzle however small the stand-in is drawn (SetScale moves the tags). Effects cannot scale: each drive kind
//   ships five SIZE BUCKETS (gen_fx.py) and the one nearest the drawn nozzle plays, with hysteresis at the edges. A
//   nozzle too small on screen for a flame shows a GLINT (a bright point + a faint streak): a far ship reads as its
//   engines, like an aircraft at night. The dreadnought's main drives fire a TIME-WARP PULSE every 1.8 s (in the fx).
//   A self-check (TAG_CHECK) compares the tag against the scaled nozzle once; if tags do not scale, flames only play on
//   the full-size ship (the v2 rule) and the log says so.
// WORMHOLES. Some flights ARRIVE through a rift where the ship would be ~worm_px pixels long, on the side the player IS
//   looking: a violet point swells into a swirling, crackling rift (1.6 s), the ship BURSTS out of it (flash, electric
//   shockwave, lens ripple), growing from the rift at speed and easing to cruise, and the rift collapses behind the
//   wing. Some LEAVE through one: it opens ahead as the ship climbs away, the ship dives in and vanishes, it collapses.
//   The rift is a camera-facing effect on a host moved every tick to its stand-in (so it stays on the ship's line even
//   while the player moves), in one of five size buckets.
// ASTEROIDS. Rocks drift across the upper sky (elevation 22..80) on great circles, tumbling, 8..40 px, growing out of
//   the distance and shrinking back into it (never a pop), singly or in loose clusters; others orbit the sky's two
//   black holes in their painted disc planes, spiral in, hide behind the shadow and are swallowed with a flash.
// SHOOTING STARS. Every 6..22 s a streak crosses the upper sky, now and then a shower from one radiant, rarely a slow
//   FIREBALL (orange or green) that breaks up at the end. Runner effects: one PlayFX each, no entity.
// THE SALUTE (61's first-jump scene): tod_jump_title_ignite + 1.6 s (real time) sends a fighter wing across the
//   blazing sign from outside the frame, and a far hauler begins its approach.
//
// v4 (user 2026-09-30: "add more but at a higher altitude. I would love the sky filled up. Maybe 1.5x more"; "if there are
// any enhancements you can make for a more atmospheric player experience lets do it"; docs/192 s12):
// THE HIGH LAYER. Every class runs a SECOND schedule (gen_lanes.js MOTION.hi -> motion() hi_*) flown in the band ABOVE the
//   low layer's (HI_ALT_MIN..HI_ALT_MAX over the player's feet instead of ALT_MIN..ALT_MAX) and allowed to cross nearly
//   overhead (HI_NEAR). The low layer the user approved is untouched: the high one ADDS about half as much traffic again.
// CONVOYS. Some hauler flights lead a freight convoy (one or two more haulers on the SAME path, a few seconds astern, a
//   little staggered); some gunship flights fly as a patrol pair. A follower is a fixed-path sortie of the lead's plan.
// THE HIGH BELT. A third of the drifts, streaks and showers start high in the sky (HIGH_PCT: 58..86 deg), the rock /
//   star / fireball rates are 1.5x, more rocks orbit the black holes.
// SATELLITES. Slow steady points of light cross the upper sky (0.2..0.5 deg/s, 70..160 s), tumbling: a small flare every
//   few seconds. A tag_origin host carries a looping point effect (four sizes, sat_fx) on the stand-in, like a rock.
//
// Dev logs: [TOD_SKY] READY / SORTIE / CONVOY / FULL / TAG_CHECK / WORM_OPEN / WORM_BURST / WORM_CLOSE / DONE / NO_LANE /
// REVEAL / ROCK / ROCK_DONE / HOLE_EAT / STAR / SHOWER / FIREBALL / SAT / SAT_DONE (dev-block output, the user's launcher
// enables it; TOD_SKY_LOG 0 before a publish).
// =============================================================================

#using scripts\shared\callbacks_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;
#using scripts\zm\zm_tod2_cybercity\_tod_sky_lanes;

#insert scripts\shared\shared.gsh;

#precache( "client_fx", "tod/sky/fx_sky_flame_plasma_capital_0" );
#precache( "client_fx", "tod/sky/fx_sky_flame_plasma_capital_1" );
#precache( "client_fx", "tod/sky/fx_sky_flame_plasma_capital_2" );
#precache( "client_fx", "tod/sky/fx_sky_flame_plasma_capital_3" );
#precache( "client_fx", "tod/sky/fx_sky_flame_plasma_capital_4" );
#precache( "client_fx", "tod/sky/fx_sky_flame_plasma_0" );
#precache( "client_fx", "tod/sky/fx_sky_flame_plasma_1" );
#precache( "client_fx", "tod/sky/fx_sky_flame_plasma_2" );
#precache( "client_fx", "tod/sky/fx_sky_flame_plasma_3" );
#precache( "client_fx", "tod/sky/fx_sky_flame_plasma_4" );
#precache( "client_fx", "tod/sky/fx_sky_flame_fire_0" );
#precache( "client_fx", "tod/sky/fx_sky_flame_fire_1" );
#precache( "client_fx", "tod/sky/fx_sky_flame_fire_2" );
#precache( "client_fx", "tod/sky/fx_sky_flame_fire_3" );
#precache( "client_fx", "tod/sky/fx_sky_flame_fire_4" );
#precache( "client_fx", "tod/sky/fx_sky_flame_fire_heavy_0" );
#precache( "client_fx", "tod/sky/fx_sky_flame_fire_heavy_1" );
#precache( "client_fx", "tod/sky/fx_sky_flame_fire_heavy_2" );
#precache( "client_fx", "tod/sky/fx_sky_flame_fire_heavy_3" );
#precache( "client_fx", "tod/sky/fx_sky_flame_fire_heavy_4" );
#precache( "client_fx", "tod/sky/fx_sky_glint_cyan_s" );
#precache( "client_fx", "tod/sky/fx_sky_glint_cyan_m" );
#precache( "client_fx", "tod/sky/fx_sky_glint_cyan_l" );
#precache( "client_fx", "tod/sky/fx_sky_glint_orange_s" );
#precache( "client_fx", "tod/sky/fx_sky_glint_orange_m" );
#precache( "client_fx", "tod/sky/fx_sky_glint_orange_l" );
#precache( "client_fx", "tod/sky/fx_sky_worm_open_0" );
#precache( "client_fx", "tod/sky/fx_sky_worm_open_1" );
#precache( "client_fx", "tod/sky/fx_sky_worm_open_2" );
#precache( "client_fx", "tod/sky/fx_sky_worm_open_3" );
#precache( "client_fx", "tod/sky/fx_sky_worm_open_4" );
#precache( "client_fx", "tod/sky/fx_sky_worm_open_5" );
#precache( "client_fx", "tod/sky/fx_sky_worm_open_6" );
#precache( "client_fx", "tod/sky/fx_sky_worm_burst_0" );
#precache( "client_fx", "tod/sky/fx_sky_worm_burst_1" );
#precache( "client_fx", "tod/sky/fx_sky_worm_burst_2" );
#precache( "client_fx", "tod/sky/fx_sky_worm_burst_3" );
#precache( "client_fx", "tod/sky/fx_sky_worm_burst_4" );
#precache( "client_fx", "tod/sky/fx_sky_worm_burst_5" );
#precache( "client_fx", "tod/sky/fx_sky_worm_burst_6" );
#precache( "client_fx", "tod/sky/fx_sky_worm_close_0" );
#precache( "client_fx", "tod/sky/fx_sky_worm_close_1" );
#precache( "client_fx", "tod/sky/fx_sky_worm_close_2" );
#precache( "client_fx", "tod/sky/fx_sky_worm_close_3" );
#precache( "client_fx", "tod/sky/fx_sky_worm_close_4" );
#precache( "client_fx", "tod/sky/fx_sky_worm_close_5" );
#precache( "client_fx", "tod/sky/fx_sky_worm_close_6" );
#precache( "client_fx", "tod/sky/fx_sky_star_a" );
#precache( "client_fx", "tod/sky/fx_sky_star_b" );
#precache( "client_fx", "tod/sky/fx_sky_star_c" );
#precache( "client_fx", "tod/sky/fx_sky_fireball_o" );
#precache( "client_fx", "tod/sky/fx_sky_fireball_g" );
#precache( "client_fx", "tod/sky/fx_sky_strobe_s" );
#precache( "client_fx", "tod/sky/fx_sky_strobe_m" );
#precache( "client_fx", "tod/sky/fx_sky_strobe_l" );
#precache( "client_fx", "tod/sky/fx_sky_beacon_s" );
#precache( "client_fx", "tod/sky/fx_sky_beacon_m" );
#precache( "client_fx", "tod/sky/fx_sky_beacon_l" );
#precache( "client_fx", "tod/sky/fx_sky_sat_xs" );
#precache( "client_fx", "tod/sky/fx_sky_sat_s" );
#precache( "client_fx", "tod/sky/fx_sky_sat_m" );
#precache( "client_fx", "tod/sky/fx_sky_sat_l" );

#namespace tod_sky_ships;

#define TOD_SKY_LOG        1        // [TOD_SKY] records; 0 before a publish
#define TOD_SKY_REV        4
#define TOD_SKY_TICK       0.1      // one update of every ship / rift / rock (script clock; the motion itself is real time)
#define TOD_SKY_DT_MIN     0.01     // a real-time step is clamped to this ...
#define TOD_SKY_DT_MAX     0.3      // ... and this (a hitch or a pause never teleports a ship)
#define TOD_SKY_ALT_MIN    1500     // a ship passes between these heights ABOVE the local player's feet
#define TOD_SKY_ALT_MAX    9000
#define TOD_SKY_NEAR       3500     // never passes closer than this (plus the ship's half width) sideways
#define TOD_SKY_FAR        14000    // and passes near enough to read as "passing the tower"
// v4 THE HIGH LAYER (the second schedule per class: gen_lanes.js MOTION.hi; the low layer above is untouched)
#define TOD_SKY_HI_ALT_MIN 9000     // a high-layer ship passes between these heights above the player's feet ...
#define TOD_SKY_HI_ALT_MAX 20000
#define TOD_SKY_HI_NEAR    1200     // ... and may cross nearly overhead (sideways, plus the ship's half width) ...
#define TOD_SKY_HI_FAR     16000    // ... but still near enough to read as "over the tower"
// v4 CONVOYS (gen_lanes.js MOTION.convoy): a follower flies the lead's path staggered by up to this sideways / up
#define TOD_SKY_CONVOY_SIDE 250
#define TOD_SKY_CONVOY_DZ  120
#define TOD_SKY_BAND_MIN   300      // the smallest altitude window worth choosing
#define TOD_SKY_EDGE       200      // stand-ins stay this far inside the sealed volume
#define TOD_SKY_BLEND      3000     // the glide / climb blend into and out of the level pass (units)
#define TOD_SKY_VIEW_COS   0.57     // cos 55 deg: a spawn bearing within this of the view is "in view"
#define TOD_SKY_FULL_K     0.999    // at or above this scale the ship is the real one
#define TOD_SKY_SOUND_K    0.6      // the engine loop starts at this scale on the way in, stops below 0.5 on the way out
#define TOD_SKY_LIGHT_RAD  0.0045   // a blinking light is at least this wide on screen (radians, ~6 px at 1080p)
#define TOD_SKY_STROBE_T   1.3      // white strobes: one double flash every ... s
#define TOD_SKY_BEACON_T   1.0      // red beacons: one pulse every ... s
#define TOD_SKY_BANK_SIGN  1        // -1 flips every bank (the one knob if the ships skid instead of banking)
// flames (LOCKSTEP with tools/sky_ships/gen_fx.py: BUCKETS 1 / 0.5 / 0.25 / 0.125 / 0.0625, GLINT 60 / 140 / 320)
#define TOD_SKY_FLAME_MIN_RAD 0.0016   // a nozzle smaller on screen than this (radius, radians, ~2.2 px) glints instead
#define TOD_SKY_GLINT_RAD  0.0042   // a far engine's glint is about this wide on screen (radians, ~6 px)
#define TOD_SKY_BUCKET_HYST 1.12    // a flame keeps its bucket until the drawn nozzle is 12 % past the bucket's edge
#define TOD_SKY_FLAME_MIN_X 0.0442  // below the smallest size bucket's range (0.0625 / sqrt 2) a nozzle glints instead
#define TOD_SKY_PX_RAD     0.000734 // one 1080p pixel at the in-game hfov (80.7 deg / 1920), radians (gen_lanes.js PX_RAD)
#define TOD_SKY_POP_PX     40       // a flight whose ship would come into or leave sight longer than this is not flown
// wormholes (LOCKSTEP with gen_fx.py WORM_BUCKETS 2 / 1 / 0.5 / 0.25 / 0.125 x WORM_R 1000)
#define TOD_SKY_WORM_OPEN  1.6      // s from the rift opening to the ship bursting through
#define TOD_SKY_WORM_GROW  0.45     // s for an emerging ship to grow from the rift to its size
#define TOD_SKY_WORM_BOOST 2.2      // an emerging ship leaves the rift at (1 + this) x its speed ...
#define TOD_SKY_WORM_BOOST_T 2.4    // ... easing back to cruise over this many s
#define TOD_SKY_WORM_LINGER 1.0     // s the rift stays open after the last ship is through
#define TOD_SKY_WORM_LEAD  1.4      // s before a departing ship reaches it, its rift opens
#define TOD_SKY_WORM_SHRINK 0.35    // s for a departing ship to vanish into the rift
#define TOD_SKY_WORM_FADE  1.4      // s the collapse plays before its host is deleted
// asteroids
#define TOD_SKY_ROCKS_MAX  9        // drifting rocks (a cluster counts as one) alive per player at once (v4: 1.5x, was 6)
#define TOD_SKY_ROCK_GAP_MIN 3.5    // s between new drifts (v4: 1.5x the rate, was 5..14)
#define TOD_SKY_ROCK_GAP_MAX 9.5
#define TOD_SKY_ROCK_EL_MIN 22      // a drifting rock never goes below this elevation (degrees): high up in the sky
// v4 THE HIGH BELT: this % of drifts and streaks are planned from the high sky (their mid / start elevation in this band)
#define TOD_SKY_HIGH_PCT   35
#define TOD_SKY_HI_BELT_MIN 58
#define TOD_SKY_HI_BELT_MAX 86
#define TOD_SKY_ROCK_MIN_RAD 0.0005 // a rock smaller on screen than this (radians, ~0.7 px) is not drawn
#define TOD_SKY_HOLE_ROCKS 1        // 0 = no rocks round the black holes
// shooting stars
#define TOD_SKY_STAR_GAP_MIN 4      // s between streaks (v4: 1.5x the rate, was 6..22)
#define TOD_SKY_STAR_GAP_MAX 15
#define TOD_SKY_SHOWER_PCT 8        // % of star events that are a shower (4..7 from one radiant)
#define TOD_SKY_BALL_GAP_MIN 55     // s between fireballs (v4: 1.5x the rate, was 80..200)
#define TOD_SKY_BALL_GAP_MAX 135
#define TOD_SKY_STAR_R_MIN 5000     // a streak is drawn this far ...
#define TOD_SKY_STAR_R_MAX 11000    // ... to this far from the camera (inside the sealed box)
#define TOD_SKY_SALUTE_DELAY 1.6    // s (real) after the jump scene's ignite before the salute spawns
// v4 THE ENTITY BUDGET: everything the fleet spawns on one client (ships, rift hosts, rocks, satellites) is counted; a new
// sortie / drift / satellite that would pass this is not started (log BUDGET). Every cap, convoy, 4-rock cluster, orbit
// and rift host at once would be ~105 (the gate computes it): the budget bites only in that pile-up, never in normal play.
#define TOD_SKY_ENT_MAX    96
// v4 satellites
#define TOD_SKY_SATS_MAX   3        // satellites crossing at once per player
#define TOD_SKY_SAT_GAP_MIN 20      // s between new satellites
#define TOD_SKY_SAT_GAP_MAX 55
#define TOD_SKY_SAT_EL_MIN 30       // a satellite never goes below this elevation (degrees)
#define TOD_SKY_SAT_RAD    0.0032   // its point is about this wide on screen (radians, ~4.4 px at 1080p)
#define TOD_SKY_SAT_FLARE  1.6      // its tumble flare is this x the point

REGISTER_SYSTEM( "tod_sky_ships", &__init__, undefined )

function __init__()
{
	level.tod_sky_classes = [];
	add_class( "dreadnought", array( "tod_sky_dreadnought", "tod_sky_dreadnought_b" ), "tod_sky_drone" );
	add_class( "hauler", array( "tod_sky_hauler", "tod_sky_hauler_b" ), "tod_sky_drone" );
	add_class( "gunship", array( "tod_sky_gunship", "tod_sky_gunship_b" ), "tod_sky_jet" );
	add_class( "fighter", array( "tod_sky_fighter", "tod_sky_fighter_b" ), "tod_sky_jet" );
	level.tod_sky_live = [];
	level.tod_sky_rocks_live = [];
	level.tod_sky_sats_live = [];
	level.tod_sky_ents = [];
	level.tod_sky_sat_def = ball_def( 4 );                              // one struct for every satellite's stand-in
	level.tod_sky_revealed = [];
	level.tod_sky_serial = 0;
	level.tod_sky_tag_ok = true;
	level.tod_sky_tag_checked = false;
	level.tod_sky_plan_why = "";
	level.tod_sky_lo = tod_sky_lanes::volume_lo() + ( TOD_SKY_EDGE, TOD_SKY_EDGE, TOD_SKY_EDGE );
	level.tod_sky_hi = tod_sky_lanes::volume_hi() - ( TOD_SKY_EDGE, TOD_SKY_EDGE, TOD_SKY_EDGE );
	level.tod_sky_blockers = tod_sky_lanes::blockers();
	level.tod_sky_rocks = tod_sky_lanes::rocks();
	level.tod_sky_holes = tod_sky_lanes::holes();
	callback::on_localclient_connect( &on_local_connect );
	level thread reveal_watch();
}

function add_class( name, models, loop_alias )
{
	def = tod_sky_lanes::motion( name );
	def.name = name;
	def.models = models;
	def.loop_alias = loop_alias;
	def.lanes = class_lanes( name );
	def.lights = tod_sky_lanes::lights( name );
	def.nozzles = tod_sky_lanes::nozzles( name );
	sz = tod_sky_lanes::size( name );
	def.back = sz[ 0 ];
	def.front = sz[ 1 ];
	def.half = sz[ 2 ];
	def.zlo = sz[ 3 ];
	def.zhi = sz[ 4 ];
	def.big = ( name == "dreadnought" || name == "hauler" );
	def.light_size = 60;                                               // a running light's own size at full scale
	if ( name == "dreadnought" ) def.light_size = 260;
	else if ( name == "hauler" ) def.light_size = 180;
	else if ( name == "gunship" ) def.light_size = 110;
	level.tod_sky_classes[ name ] = def;
}

function class_lanes( name )
{
	if ( name == "dreadnought" ) return tod_sky_lanes::dreadnought();
	if ( name == "hauler" ) return tod_sky_lanes::hauler();
	if ( name == "gunship" ) return tod_sky_lanes::gunship();
	return tod_sky_lanes::fighter();
}

// ---- the effect names (literals keep the FX lint and the precache honest; LOCKSTEP with gen_fx.py) ----------------
// kind: 0 plasma_capital (dreadnought mains), 1 plasma, 2 fire (fighter), 3 fire_heavy (hauler)
function flame_fx( kind, b )
{
	if ( kind == 0 )
	{
		if ( b == 0 ) return "tod/sky/fx_sky_flame_plasma_capital_0";
		if ( b == 1 ) return "tod/sky/fx_sky_flame_plasma_capital_1";
		if ( b == 2 ) return "tod/sky/fx_sky_flame_plasma_capital_2";
		if ( b == 3 ) return "tod/sky/fx_sky_flame_plasma_capital_3";
		return "tod/sky/fx_sky_flame_plasma_capital_4";
	}
	if ( kind == 1 )
	{
		if ( b == 0 ) return "tod/sky/fx_sky_flame_plasma_0";
		if ( b == 1 ) return "tod/sky/fx_sky_flame_plasma_1";
		if ( b == 2 ) return "tod/sky/fx_sky_flame_plasma_2";
		if ( b == 3 ) return "tod/sky/fx_sky_flame_plasma_3";
		return "tod/sky/fx_sky_flame_plasma_4";
	}
	if ( kind == 2 )
	{
		if ( b == 0 ) return "tod/sky/fx_sky_flame_fire_0";
		if ( b == 1 ) return "tod/sky/fx_sky_flame_fire_1";
		if ( b == 2 ) return "tod/sky/fx_sky_flame_fire_2";
		if ( b == 3 ) return "tod/sky/fx_sky_flame_fire_3";
		return "tod/sky/fx_sky_flame_fire_4";
	}
	if ( b == 0 ) return "tod/sky/fx_sky_flame_fire_heavy_0";
	if ( b == 1 ) return "tod/sky/fx_sky_flame_fire_heavy_1";
	if ( b == 2 ) return "tod/sky/fx_sky_flame_fire_heavy_2";
	if ( b == 3 ) return "tod/sky/fx_sky_flame_fire_heavy_3";
	return "tod/sky/fx_sky_flame_fire_heavy_4";
}

// a far engine: cyan for the plasma drives, orange for the fire drives; sized to stay ~6 px on screen
function glint_fx( kind, size )
{
	if ( kind <= 1 )
	{
		if ( size < 90 ) return "tod/sky/fx_sky_glint_cyan_s";
		if ( size < 200 ) return "tod/sky/fx_sky_glint_cyan_m";
		return "tod/sky/fx_sky_glint_cyan_l";
	}
	if ( size < 90 ) return "tod/sky/fx_sky_glint_orange_s";
	if ( size < 200 ) return "tod/sky/fx_sky_glint_orange_m";
	return "tod/sky/fx_sky_glint_orange_l";
}

// phase: 0 open (looping until stopped), 1 burst, 2 close
function worm_fx( phase, b )
{
	if ( phase == 0 )
	{
		if ( b == 0 ) return "tod/sky/fx_sky_worm_open_0";
		if ( b == 1 ) return "tod/sky/fx_sky_worm_open_1";
		if ( b == 2 ) return "tod/sky/fx_sky_worm_open_2";
		if ( b == 3 ) return "tod/sky/fx_sky_worm_open_3";
		if ( b == 4 ) return "tod/sky/fx_sky_worm_open_4";
		if ( b == 5 ) return "tod/sky/fx_sky_worm_open_5";
		return "tod/sky/fx_sky_worm_open_6";
	}
	if ( phase == 1 )
	{
		if ( b == 0 ) return "tod/sky/fx_sky_worm_burst_0";
		if ( b == 1 ) return "tod/sky/fx_sky_worm_burst_1";
		if ( b == 2 ) return "tod/sky/fx_sky_worm_burst_2";
		if ( b == 3 ) return "tod/sky/fx_sky_worm_burst_3";
		if ( b == 4 ) return "tod/sky/fx_sky_worm_burst_4";
		if ( b == 5 ) return "tod/sky/fx_sky_worm_burst_5";
		return "tod/sky/fx_sky_worm_burst_6";
	}
	if ( b == 0 ) return "tod/sky/fx_sky_worm_close_0";
	if ( b == 1 ) return "tod/sky/fx_sky_worm_close_1";
	if ( b == 2 ) return "tod/sky/fx_sky_worm_close_2";
	if ( b == 3 ) return "tod/sky/fx_sky_worm_close_3";
	if ( b == 4 ) return "tod/sky/fx_sky_worm_close_4";
	if ( b == 5 ) return "tod/sky/fx_sky_worm_close_5";
	return "tod/sky/fx_sky_worm_close_6";
}

function star_fx( v )
{
	if ( v == 0 ) return "tod/sky/fx_sky_star_a";
	if ( v == 1 ) return "tod/sky/fx_sky_star_b";
	return "tod/sky/fx_sky_star_c";
}

function ball_fx( green )
{
	if ( green ) return "tod/sky/fx_sky_fireball_g";
	return "tod/sky/fx_sky_fireball_o";
}

function light_fx( kind, size )
{
	if ( kind == "b" )
	{
		if ( size < 70 ) return "tod/sky/fx_sky_beacon_s";
		if ( size < 170 ) return "tod/sky/fx_sky_beacon_m";
		return "tod/sky/fx_sky_beacon_l";
	}
	if ( size < 70 ) return "tod/sky/fx_sky_strobe_s";
	if ( size < 170 ) return "tod/sky/fx_sky_strobe_m";
	return "tod/sky/fx_sky_strobe_l";
}

function on_local_connect( localClientNum )
{
	level.tod_sky_live[ localClientNum ] = [];
	level.tod_sky_rocks_live[ localClientNum ] = 0;
	n = 0;
	caps_lo = 0;
	caps_hi = 0;
	foreach ( def in level.tod_sky_classes )
	{
		level.tod_sky_live[ localClientNum ][ live_key( def, 0 ) ] = 0;
		level.tod_sky_live[ localClientNum ][ live_key( def, 1 ) ] = 0;
		n += def.lanes.size;
		caps_lo += def.cap;
		caps_hi += def.hi_cap;
		level thread class_loop( localClientNum, def, 0 );
		level thread class_loop( localClientNum, def, 1 );                 // v4 the high layer
	}
	level.tod_sky_sats_live[ localClientNum ] = 0;
	level.tod_sky_ents[ localClientNum ] = 0;
	level thread rock_loop( localClientNum );
	if ( TOD_SKY_HOLE_ROCKS )
	{
		for ( h = 0; h < level.tod_sky_holes.size; h++ )
			level thread hole_loop( localClientNum, level.tod_sky_holes[ h ] );
	}
	level thread star_loop( localClientNum );
	level thread fireball_loop( localClientNum );
	level thread satellite_loop( localClientNum );
	log( "READY rev=" + TOD_SKY_REV + " rock_math=case_safe client=" + localClientNum + " classes=" + level.tod_sky_classes.size + " lanes=" + n
		+ " blockers=" + level.tod_sky_blockers.size + " rocks=" + level.tod_sky_rocks.size + " holes=" + level.tod_sky_holes.size
		+ " high_layer=1 caps_low=" + caps_lo + " caps_high=" + caps_hi + " hi_alt=" + TOD_SKY_HI_ALT_MIN + ".." + TOD_SKY_HI_ALT_MAX
		+ " rocks_max=" + TOD_SKY_ROCKS_MAX + " high_pct=" + TOD_SKY_HIGH_PCT + " sats_max=" + TOD_SKY_SATS_MAX + " ent_max=" + TOD_SKY_ENT_MAX );
}

// ---- v4 the entity budget (pure: the gate exercises them) ----------------------------------------------------------
// Every client entity the fleet spawns is counted here at its spawn and uncounted at its Delete.
function ents_add( localClientNum, n )
{
	level.tod_sky_ents[ localClientNum ] += n;
}

// Can n more be spawned on this client without passing the budget?
function ents_free( localClientNum, n )
{
	return level.tod_sky_ents[ localClientNum ] + n <= TOD_SKY_ENT_MAX;
}

// One loop per class per TIER per local client (v4: tier 0 = the low layer, 1 = the high layer, each with its own
// schedule and cap from gen_lanes.js MOTION / MOTION.hi): wait a random gap (real time), launch a flight if under the
// tier's cap, repeat.
function class_loop( localClientNum, def, tier )
{
	level endon( "tod_sky_stop" );
	s = sched( def, tier );
	key = live_key( def, tier );
	waitrealtime( s[ 0 ] + RandomFloatRange( 0, s[ 1 ] * 0.5 ) );
	while ( true )
	{
		if ( level.tod_sky_live[ localClientNum ][ key ] < s[ 3 ] )
			level thread sortie( localClientNum, def, undefined, tier );
		waitrealtime( RandomFloatRange( s[ 1 ], s[ 2 ] ) );
	}
}

// A tier's schedule: array( first, gap_min, gap_max, cap ). Pure.
function sched( def, tier )
{
	if ( isdefined( tier ) && tier ) return array( def.hi_first, def.hi_gap_min, def.hi_gap_max, def.hi_cap );
	return array( def.first, def.gap_min, def.gap_max, def.cap );
}

// The live counter's key: one per class per tier. Pure.
function live_key( def, tier )
{
	if ( isdefined( tier ) && tier ) return def.name + "_high";
	return def.name;
}

function tier_name( tier )
{
	if ( isdefined( tier ) && tier ) return "high";
	return "low";
}

// ---- small maths ----------------------------------------------------------------------------------------------
function fmin( a, b ) { if ( a < b ) return a; return b; }
function fmax( a, b ) { if ( a > b ) return a; return b; }
function fclamp( x, a, b ) { return fmin( b, fmax( a, x ) ); }
function fmod( x, m ) { return x - int( x / m ) * m; }      // x >= 0
function vdot( a, b ) { return a[ 0 ] * b[ 0 ] + a[ 1 ] * b[ 1 ] + a[ 2 ] * b[ 2 ]; }
function vcross( a, b ) { return ( a[ 1 ] * b[ 2 ] - a[ 2 ] * b[ 1 ], a[ 2 ] * b[ 0 ] - a[ 0 ] * b[ 2 ], a[ 0 ] * b[ 1 ] - a[ 1 ] * b[ 0 ] ); }
function vnorm( v )
{
	l = Length( v );
	if ( l < 0.000001 ) return ( 1, 0, 0 );
	return v * ( 1.0 / l );
}
// a unit direction from a yaw and an elevation (degrees): yaw 0 = +X, 90 = +Y, elevation up
function dir_ye( yaw, el ) { return ( Cos( el ) * Cos( yaw ), Cos( el ) * Sin( yaw ), Sin( el ) ); }
function smooth( x ) { x = fclamp( x, 0, 1 ); return x * x * ( 3 - 2 * x ); }

// The real-time step since `last` (ms): clamped, so a hitch or a paused menu never jumps anything.
function rt_step( last )
{
	return fclamp( ( GetRealTime() - last ) / 1000.0, TOD_SKY_DT_MIN, TOD_SKY_DT_MAX );
}

// ---- lanes ------------------------------------------------------------------------------------------------------
function seg_dist2d( p, a, b )
{
	dx = b[ 0 ] - a[ 0 ];
	dy = b[ 1 ] - a[ 1 ];
	len2 = dx * dx + dy * dy;
	t = 0;
	if ( len2 > 0 )
		t = fmin( 1, fmax( 0, ( ( p[ 0 ] - a[ 0 ] ) * dx + ( p[ 1 ] - a[ 1 ] ) * dy ) / len2 ) );
	cx = a[ 0 ] + dx * t - p[ 0 ];
	cy = a[ 1 ] + dy * t - p[ 1 ];
	return Sqrt( cx * cx + cy * cy );
}

// A lane + an altitude window above the player, passing at a comfortable distance. v4: tier 0 (the low layer) wants
// ALT_MIN..ALT_MAX up and NEAR..FAR sideways, as always; tier 1 (the high layer) wants HI_ALT_MIN..HI_ALT_MAX up and may
// cross nearly overhead (HI_NEAR..HI_FAR). Relaxed passes widen the window (any band above the tier's floor - for the
// high layer at any distance - then any band at all) so a flight always has somewhere to go.
function pick_lane( def, p, tier )
{
	high = isdefined( tier ) && tier;
	alt_lo = TOD_SKY_ALT_MIN;
	alt_hi = TOD_SKY_ALT_MAX;
	d_near = TOD_SKY_NEAR;
	d_far = TOD_SKY_FAR;
	if ( high )
	{
		alt_lo = TOD_SKY_HI_ALT_MIN;
		alt_hi = TOD_SKY_HI_ALT_MAX;
		d_near = TOD_SKY_HI_NEAR;
		d_far = TOD_SKY_HI_FAR;
	}
	for ( pass = 0; pass < 3; pass++ )
	{
		lo_want = p[ 2 ] + alt_lo;
		hi_want = p[ 2 ] + alt_hi;
		if ( pass == 1 )
		{
			hi_want = p[ 2 ] + 30000;
			if ( high ) hi_want = p[ 2 ] + 100000;
		}
		if ( pass == 2 ) { lo_want = -100000; hi_want = 100000; }
		good = [];
		for ( i = 0; i < def.lanes.size; i++ )
		{
			l = def.lanes[ i ];
			if ( pass == 0 || ( pass == 1 && !high ) )
			{
				d = seg_dist2d( p, l[ 0 ], l[ 1 ] );
				if ( d < d_near + def.half || d > d_far ) continue;
			}
			bands = l[ 2 ];
			for ( k = 0; k < bands.size; k++ )
			{
				lo = fmax( bands[ k ][ 0 ], lo_want );
				hi = fmin( bands[ k ][ 1 ], hi_want );
				if ( hi - lo >= TOD_SKY_BAND_MIN )
					good[ good.size ] = array( i, lo, fmin( hi, lo + ( alt_hi - alt_lo ) ) );
			}
		}
		if ( good.size )
		{
			g = good[ RandomInt( good.size ) ];
			s = SpawnStruct();
			s.id = g[ 0 ];
			s.a = def.lanes[ g[ 0 ] ][ 0 ];
			s.b = def.lanes[ g[ 0 ] ][ 1 ];
			s.z = RandomFloatRange( g[ 1 ], g[ 2 ] );
			s.relaxed = pass;
			return s;
		}
	}
	return undefined;
}

// ---- the flight path ------------------------------------------------------------------------------------------------
function make_path( def, a, b, z, speed, glide, climb )
{
	p = SpawnStruct();
	dx = b[ 0 ] - a[ 0 ];
	dy = b[ 1 ] - a[ 1 ];
	p.len = Sqrt( dx * dx + dy * dy );
	p.dir = ( dx / p.len, dy / p.len, 0 );
	p.side = ( 0 - p.dir[ 1 ], p.dir[ 0 ], 0 );
	p.a = ( a[ 0 ], a[ 1 ], 0 );
	p.z = z;
	p.speed = speed;
	p.xs = def.xs;
	p.yaw = VectorToAngles( p.dir )[ 1 ];
	p.glide = glide;
	p.climb = climb;
	p.tan_in = Sin( glide ) / Cos( glide );
	p.tan_out = Sin( climb ) / Cos( climb );
	p.weave_a = def.weave_a;
	p.weave_t = def.weave_t;
	p.bob_a = def.bob_a;
	p.bob_t = def.bob_t;
	p.bank = def.bank * TOD_SKY_BANK_SIGN;
	p.sway_r = def.sway_roll;
	p.sway_rt = def.sway_roll_t;
	p.sway_p = def.sway_pitch;
	p.sway_pt = def.sway_pitch_t;
	p.ph1 = RandomFloatRange( 0, 360 );
	p.ph2 = RandomFloatRange( 0, 360 );
	p.ph3 = RandomFloatRange( 0, 360 );
	p.ph4 = RandomFloatRange( 0, 360 );
	return p;
}

function glide_rise( d, tan_g )
{
	if ( d < TOD_SKY_BLEND ) return tan_g * d * d / ( 2 * TOD_SKY_BLEND );
	return tan_g * ( d - TOD_SKY_BLEND / 2 );
}

// The virtual ship at along-path distance s and flight time t: array( origin, angles ). Angles ( pitch, yaw, roll ),
// pitch > 0 = nose DOWN.
function path_pose( p, s, t )
{
	zz = p.z;
	pitch = 0;
	if ( s < 0 )
	{
		zz += glide_rise( 0 - s, p.tan_in );
		pitch = p.glide * fmin( 1, ( 0 - s ) / TOD_SKY_BLEND );
	}
	else if ( s > p.len )
	{
		zz += glide_rise( s - p.len, p.tan_out );
		pitch = 0 - p.climb * fmin( 1, ( s - p.len ) / TOD_SKY_BLEND );
	}
	ph = 360 * t / p.weave_t + p.ph1;
	w = p.weave_a * Sin( ph );
	wv = p.weave_a * ( 6.283185 / p.weave_t ) * Cos( ph );             // sideways speed (units/s)
	bob = p.bob_a * Sin( 360 * t / p.bob_t + p.ph2 );
	org = p.a + p.dir * s + p.side * w + ( 0, 0, zz + bob );
	yaw = p.yaw + 57.29578 * wv / p.speed;                              // the nose follows the curve (small angle)
	roll = p.bank * Sin( ph ) + p.sway_r * Sin( 360 * t / p.sway_rt + p.ph3 );
	pitch += p.sway_p * Sin( 360 * t / p.sway_pt + p.ph4 );
	return array( org, ( pitch, yaw, roll ) );
}

// One ship of a wing: the lead's pose plus its formation slot (back, port, up), turned with the lead's heading.
function wing_pose( p, s, t, off )
{
	pose = path_pose( p, s, t );
	ang = pose[ 1 ];
	ff = AnglesToForward( ( 0, ang[ 1 ], 0 ) );
	fr = AnglesToRight( ( 0, ang[ 1 ], 0 ) );
	return array( pose[ 0 ] + ff * off[ 0 ] - fr * off[ 1 ] + ( 0, 0, off[ 2 ] ), ang );
}

// Fly the way whose far approach is OUT of the player's view: the a->b approach bearing is -dir. true = swap to b->a.
function choose_way( a, b, fwd )
{
	dx = b[ 0 ] - a[ 0 ];
	dy = b[ 1 ] - a[ 1 ];
	L = Sqrt( dx * dx + dy * dy );
	f2 = Sqrt( fwd[ 0 ] * fwd[ 0 ] + fwd[ 1 ] * fwd[ 1 ] );
	if ( f2 < 0.01 || L < 1 ) return RandomInt( 2 ) == 1;
	seen = ( 0 - ( fwd[ 0 ] * dx + fwd[ 1 ] * dy ) ) / ( f2 * L );         // how much -dir faces the view
	if ( seen > TOD_SKY_VIEW_COS ) return true;
	if ( seen < 0 - TOD_SKY_VIEW_COS ) return false;
	return RandomInt( 2 ) == 1;
}

// Far out the ship moves at speed * (1 + d / xs): it looms steadily, slows as it arrives and speeds away.
function path_speed( p, s )
{
	if ( s < 0 ) return p.speed * ( 1 + ( 0 - s ) / p.xs );
	if ( s > p.len ) return p.speed * ( 1 + ( s - p.len ) / p.xs );
	return p.speed;
}

// A ship just out of a rift leaves it at (1 + BOOST) x speed, easing back to cruise over BOOST_T s.
function worm_boost( te )
{
	if ( te < 0 ) return 1;
	u = 1 - fmin( 1, te / TOD_SKY_WORM_BOOST_T );
	return 1 + TOD_SKY_WORM_BOOST * u * u;
}

// ---- the scaled stand-in ----------------------------------------------------------------------------------------
// -> array( drawn origin, scale k, hidden ). The box corners (back/front, +-half, zlo/zhi, rotated by angles) stay inside
// the sealed volume: along the camera ray each corner moves linearly with the drawn distance r, so the largest r is a
// closed form per corner and axis. k = r / D.
function stand_in( def, org, angles, cam )
{
	dv = org - cam;
	D = Length( dv );
	if ( D < 1 ) D = 1;
	u = dv * ( 1.0 / D );
	f = AnglesToForward( angles );
	rt = AnglesToRight( angles );
	up = AnglesToUp( angles );
	lo = level.tod_sky_lo;
	hi = level.tod_sky_hi;
	r = D;
	for ( i = 0; i < 8; i++ )
	{
		cx = def.front;
		if ( i % 2 ) cx = 0 - def.back;
		cy = def.half;
		if ( int( i / 2 ) % 2 ) cy = 0 - def.half;
		cz = def.zhi;
		if ( int( i / 4 ) ) cz = def.zlo;
		w = u + ( f * cx - rt * cy + up * cz ) * ( 1.0 / D );
		for ( j = 0; j < 3; j++ )
		{
			if ( w[ j ] > 0.000001 ) r = fmin( r, ( hi[ j ] - cam[ j ] ) / w[ j ] );
			else if ( w[ j ] < -0.000001 ) r = fmin( r, ( lo[ j ] - cam[ j ] ) / w[ j ] );
		}
	}
	r = fmax( r, 1 );
	k = r / D;
	drawn = cam + u * r;
	hidden = false;
	if ( k < TOD_SKY_FULL_K )
	{
		lx = fmax( def.front, def.back );
		lz = fmax( abs( def.zlo ), abs( def.zhi ) );
		ex = k * ( abs( f[ 0 ] ) * lx + abs( rt[ 0 ] ) * def.half + abs( up[ 0 ] ) * lz );
		ey = k * ( abs( f[ 1 ] ) * lx + abs( rt[ 1 ] ) * def.half + abs( up[ 1 ] ) * lz );
		ez = k * ( abs( f[ 2 ] ) * lx + abs( rt[ 2 ] ) * def.half + abs( up[ 2 ] ) * lz );
		foreach ( b in level.tod_sky_blockers )
		{
			if ( drawn[ 0 ] + ex < b[ 0 ][ 0 ] || drawn[ 0 ] - ex > b[ 1 ][ 0 ] ) continue;
			if ( drawn[ 1 ] + ey < b[ 0 ][ 1 ] || drawn[ 1 ] - ey > b[ 1 ][ 1 ] ) continue;
			if ( drawn[ 2 ] + ez < b[ 0 ][ 2 ] || drawn[ 2 ] - ez > b[ 1 ][ 2 ] ) continue;
			hidden = true;
			break;
		}
	}
	return array( drawn, k, hidden );
}

// A cube-bounded object (a rift, a rock) for stand_in: +-r on every axis.
function ball_def( r )
{
	d = SpawnStruct();
	d.front = r;
	d.back = r;
	d.half = r;
	d.zhi = r;
	d.zlo = 0 - r;
	return d;
}

// ---- the flames ---------------------------------------------------------------------------------------------------
// x = the drawn nozzle radius / the kind's reference radius. Buckets 1 / 0.5 / 0.25 / 0.125 / 0.0625, each covering
// x within a factor sqrt(2) of it; the current bucket holds until x is BUCKET_HYST past its edge.
function flame_bucket( x, prev )
{
	b = 4;
	if ( x > 0.7071 ) b = 0;
	else if ( x > 0.3536 ) b = 1;
	else if ( x > 0.1768 ) b = 2;
	else if ( x > 0.0884 ) b = 3;
	if ( prev >= 0 && prev != b )
	{
		c = 1.0;
		for ( i = 0; i < prev; i++ ) c = c * 0.5;
		if ( x < c * 1.4142 * TOD_SKY_BUCKET_HYST && x > c * 0.7071 / TOD_SKY_BUCKET_HYST ) b = prev;
	}
	return b;
}

// What one nozzle should show: array( effect or "", bucket ). nz = array( tag, radius, kind, main, ref ); k = the drawn
// scale (x the emergence factor), rd = the drawn distance from the camera.
function engine_want( nz, k, rd, prevb, tagok )
{
	if ( !tagok && k < TOD_SKY_FULL_K ) return array( "", -1 );
	x = k * nz[ 1 ] / nz[ 4 ];
	x_min = TOD_SKY_FLAME_MIN_X;
	if ( prevb == 4 ) x_min = TOD_SKY_FLAME_MIN_X / TOD_SKY_BUCKET_HYST;
	if ( k * nz[ 1 ] >= fmax( rd, 1 ) * TOD_SKY_FLAME_MIN_RAD && x >= x_min )
	{
		b = flame_bucket( x, prevb );
		return array( flame_fx( nz[ 2 ], b ), b );
	}
	if ( nz[ 3 ] && tagok && k > 0.0001 ) return array( glint_fx( nz[ 2 ], rd * TOD_SKY_GLINT_RAD ), -1 );
	return array( "", -1 );
}

// Keep every nozzle's effect in step with what it should show (a change stops the old one: its particles finish).
function engines( localClientNum, def, ship, k, rd, shown )
{
	for ( i = 0; i < def.nozzles.size; i++ )
	{
		w = array( "", -1 );
		if ( shown ) w = engine_want( def.nozzles[ i ], k, rd, ship.tod_sky_nzb[ i ], level.tod_sky_tag_ok );
		if ( w[ 0 ] == ship.tod_sky_nzk[ i ] ) continue;
		if ( isdefined( ship.tod_sky_nzf[ i ] ) )
		{
			StopFX( localClientNum, ship.tod_sky_nzf[ i ] );
			ship.tod_sky_nzf[ i ] = undefined;
		}
		ship.tod_sky_nzk[ i ] = w[ 0 ];
		ship.tod_sky_nzb[ i ] = w[ 1 ];
		if ( w[ 0 ] == "" ) continue;
		if ( !IS_TRUE( ship.tod_sky_dobj ) )
		{
			ship util::waittill_dobj( localClientNum );
			if ( !isdefined( ship ) ) return;
			ship.tod_sky_dobj = true;
		}
		ship.tod_sky_nzf[ i ] = PlayFXOnTag( localClientNum, w[ 0 ], ship, def.nozzles[ i ][ 0 ] );
		ship.tod_sky_swaps++;
	}
}

function engines_off( localClientNum, ship )
{
	if ( !isdefined( ship ) || !isdefined( ship.tod_sky_nzf ) ) return;
	for ( i = 0; i < ship.tod_sky_nzk.size; i++ )
	{
		if ( isdefined( ship.tod_sky_nzf[ i ] ) ) StopFX( localClientNum, ship.tod_sky_nzf[ i ] );
		ship.tod_sky_nzf[ i ] = undefined;
		ship.tod_sky_nzk[ i ] = "";
		ship.tod_sky_nzb[ i ] = -1;
	}
}

// Once per game: does the nozzle TAG move with SetScale? Compare it with the scaled nozzle on a mid-size stand-in.
function tag_check( def, ship )
{
	if ( level.tod_sky_tag_checked || !def.nozzles.size ) return;
	if ( ship.tod_sky_k < 0.05 || ship.tod_sky_k > 0.8 ) return;
	nz = def.nozzles[ 0 ];
	got = ship GetTagOrigin( nz[ 0 ] );
	if ( !isdefined( got ) ) return;
	level.tod_sky_tag_checked = true;
	f = AnglesToForward( ship.angles );
	rt = AnglesToRight( ship.angles );
	up = AnglesToUp( ship.angles );
	loc = f * nz[ 5 ] - rt * nz[ 6 ] + up * nz[ 7 ];
	want = ship.origin + loc * ship.tod_sky_k;
	err = Length( got - want );
	full = Length( loc ) * ( 1 - ship.tod_sky_k );                      // the error if the tag did NOT scale
	level.tod_sky_tag_ok = err < 0.25 * full + 8;
	log( "TAG_CHECK ship=" + def.name + " k=" + ship.tod_sky_k + " err=" + err + " unscaled_err=" + full + " scales=" + level.tod_sky_tag_ok
		+ " (flames on stand-ins " + level.tod_sky_tag_ok + ")" );
}

// ---- wormholes ------------------------------------------------------------------------------------------------------
// The rift's size bucket for a drawn radius (units): 2000 / 1000 / 500 / 250 / 125 / 62.5 / 31.25, nearest by ratio.
function worm_bucket( rad )
{
	if ( rad > 1414 ) return 0;
	if ( rad > 707 ) return 1;
	if ( rad > 354 ) return 2;
	if ( rad > 177 ) return 3;
	if ( rad > 88.4 ) return 4;
	if ( rad > 44.2 ) return 5;
	return 6;
}

function rift_make( def, pv, cam )
{
	r = SpawnStruct();
	r.pv = pv;
	r.rad = def.worm_r;
	r.bdef = ball_def( def.worm_r );
	si = stand_in( r.bdef, pv, ( 0, 0, 0 ), cam );
	r.drawn = si[ 0 ];
	r.k = si[ 1 ];
	r.hidden = si[ 2 ];
	r.b = worm_bucket( def.worm_r * si[ 1 ] );
	r.state = 0;                                                        // 0 planned, 1 open, 2 burst, 3 closing, 4 gone
	return r;
}

function rift_open( localClientNum, r, serial, why )
{
	r.host = spawn( localClientNum, r.drawn, "script_model" );
	ents_add( localClientNum, 1 );
	r.host SetModel( "tag_origin" );
	r.host util::waittill_dobj( localClientNum );
	r.fx = PlayFXOnTag( localClientNum, worm_fx( 0, r.b ), r.host, "tag_origin" );
	PlaySound( localClientNum, "tod_sky_worm_open", r.drawn );
	r.state = 1;
	log( "WORM_OPEN n=" + serial + " " + why + " at=" + r.drawn + " k=" + r.k + " bucket=" + r.b + " virtual=" + r.pv );
}

function rift_follow( r, cam )
{
	if ( !isdefined( r.host ) ) return;
	si = stand_in( r.bdef, r.pv, ( 0, 0, 0 ), cam );
	r.drawn = si[ 0 ];
	r.host MoveTo( si[ 0 ], TOD_SKY_TICK * 1.25, 0, 0 );
}

function rift_burst( localClientNum, r, serial )
{
	if ( isdefined( r.host ) ) PlayFXOnTag( localClientNum, worm_fx( 1, r.b ), r.host, "tag_origin" );
	PlaySound( localClientNum, "tod_sky_worm_burst", r.drawn );
	r.state = 2;
	log( "WORM_BURST n=" + serial + " at=" + r.drawn );
}

function rift_close( localClientNum, r, serial, t )
{
	if ( isdefined( r.fx ) ) StopFX( localClientNum, r.fx );
	r.fx = undefined;
	if ( isdefined( r.host ) ) PlayFXOnTag( localClientNum, worm_fx( 2, r.b ), r.host, "tag_origin" );
	PlaySound( localClientNum, "tod_sky_worm_close", r.drawn );
	r.state = 3;
	r.t_close = t;
	log( "WORM_CLOSE n=" + serial + " at=" + r.drawn );
}

function rift_end( localClientNum, r )
{
	if ( !isdefined( r ) ) return;
	if ( isdefined( r.fx ) ) StopFX( localClientNum, r.fx );
	r.fx = undefined;
	if ( isdefined( r.host ) )
	{
		r.host Delete();
		ents_add( localClientNum, -1 );
	}
	r.host = undefined;
	r.state = 4;
}

// ---- the plan of one flight (pure: the gate runs it) ---------------------------------------------------------------
// -> struct: p, approach, depart, worm_in, worm_out, lane, relaxed, reveal, tries. fixed = a reveal struct or undefined.
// A flight that would come into (or leave) sight big from where the player is (a structure hides its approach, say the
// crown round a player in the crown hall) is re-planned: other lanes, then the other way round. If every try would pop,
// no ship flies this time (level.tod_sky_plan_why says why).
function flight_plan( def, fixed, porg, fwd, cam, tier )
{
	if ( isdefined( fixed ) )
	{
		f = SpawnStruct();
		f.worm_in = false;
		f.worm_out = false;
		f.lane = -1;
		f.relaxed = 0;
		f.reveal = true;
		f.tries = 1;
		f.p = make_path( def, fixed.a, fixed.b, fixed.a[ 2 ], fixed.speed, fixed.glide, fixed.climb );
		f.approach = fixed.approach;
		f.depart = fmax( fixed.approach, def.approach );
		return f;
	}
	level.tod_sky_plan_why = "no_lane";
	for ( attempt = 0; attempt < 8; attempt++ )
	{
		f = plan_once( def, porg, fwd, cam, attempt >= 5, tier );          // other lanes first, the other way round last
		if ( !isdefined( f ) ) return undefined;
		f.tries = attempt + 1;
		if ( !flight_pops( def, f, cam ) ) return f;
	}
	level.tod_sky_plan_why = "pops";
	return undefined;
}

// Would the lead ship come into or leave sight longer than POP_PX on screen (a hidden <-> shown change of its stand-in,
// sampled every second of the flight from the planning camera)? A rift hides the arrival / the departure itself.
// v4: a change is judged at BOTH samples round it (the larger size): a departing ship accelerates, so between two samples
// it can go from 54 px in sight to 30 px behind a structure (the high layer's fighters over the crown did). And a rift
// departure's FALLBACK (the rift found hidden at flight time: the ship flies out instead) is sampled too, out to the
// normal departure distance - a v3 flight once flew out behind the crown at 59 px that way.
function flight_pops( def, f, cam )
{
	p = f.p;
	s = 0 - f.approach;
	s_end = p.len + fmax( f.depart, def.approach );
	t = 0;
	was = f.worm_in;                                                    // a rift arrival starts in sight: in the rift
	first = !f.worm_in;
	px_was = 0;
	for ( n = 0; n < 600 && s <= s_end; n++ )
	{
		pose = path_pose( p, s, t );
		si = stand_in( def, pose[ 0 ], pose[ 1 ], cam );
		shown = !si[ 2 ];
		px = si[ 1 ] * ( def.front + def.back ) / fmax( Length( si[ 0 ] - cam ), 1 ) / TOD_SKY_PX_RAD;
		if ( !first && shown != was && fmax( px_was, px ) > TOD_SKY_POP_PX ) return true;
		first = false;
		was = shown;
		px_was = px;
		boost = 1;
		if ( f.worm_in ) boost = worm_boost( t );
		s += path_speed( p, s ) * boost;
		t += 1;
	}
	return false;
}

function plan_once( def, porg, fwd, cam, flip, tier )
{
	f = SpawnStruct();
	f.worm_in = false;
	f.worm_out = false;
	f.lane = -1;
	f.relaxed = 0;
	f.reveal = false;
	pick = pick_lane( def, porg, tier );
	if ( !isdefined( pick ) ) return undefined;
	f.lane = pick.id;
	f.relaxed = pick.relaxed;
	f.worm_in = RandomInt( 100 ) < def.worm_in;
	f.worm_out = RandomInt( 100 ) < def.worm_out;
	a = pick.a;
	b = pick.b;
	// a normal arrival comes in from OUT of view (it never pops in); a rift arrival is a show: it opens IN view
	swap = choose_way( a, b, fwd );
	if ( f.worm_in ) swap = !swap;
	if ( flip ) swap = !swap;                                          // a re-plan: the other way round
	if ( swap )
	{
		t0 = a;
		a = b;
		b = t0;
	}
	f.p = make_path( def, a, b, pick.z, def.speed, RandomFloatRange( def.glide_min, def.glide_max ), RandomFloatRange( def.climb_min, def.climb_max ) );
	f.approach = def.approach;
	f.depart = def.approach;
	if ( f.worm_in )
	{
		f.approach = def.worm_approach;
		f.rin = rift_make( def, path_pose( f.p, 0 - f.approach, 0 )[ 0 ], cam );
		if ( f.rin.hidden )
		{
			f.worm_in = false;                                          // a structure hides it: arrive normally
			f.approach = def.approach;
			f.rin = undefined;
		}
	}
	if ( f.worm_out )
	{
		// v4: like the arrival, the departure rift is tried from the planning camera: a structure would hide it -> fly out
		rout = rift_make( def, path_pose( f.p, f.p.len + def.worm_approach, 0 )[ 0 ], cam );
		if ( rout.hidden ) f.worm_out = false;
		else f.depart = def.worm_approach;
	}
	return f;
}

// ---- v4 convoys ----------------------------------------------------------------------------------------------------
// A follower's fixed path: the lead's pass (plan.p) shifted `side` units sideways and `dz` up, with the lead's speed,
// glide, climb and approach, so it flies the same line a few seconds astern. Pure: the gate flies it.
function convoy_fixed( def, plan, side, dz )
{
	p = plan.p;
	f = SpawnStruct();
	f.a = p.a + p.side * side + ( 0, 0, p.z + dz );
	f.b = f.a + p.dir * p.len;
	f.speed = p.speed;
	f.glide = p.glide;
	f.climb = p.climb;
	f.approach = plan.approach;
	f.convoy = true;
	return f;
}

// The followers of a lead flight: n more sorties of the same class on the lead's path, convoy_gap s apart (a little
// jittered), each staggered a little sideways and up. They count against the lead's tier like any sortie.
function convoy_followers( localClientNum, def, plan, n, tier, lead )
{
	level endon( "tod_sky_stop" );
	log( "CONVOY n=" + lead + " client=" + localClientNum + " ship=" + def.name + " tier=" + tier_name( tier ) + " followers=" + n + " gap=" + def.convoy_gap );
	for ( i = 0; i < n; i++ )
	{
		waitrealtime( def.convoy_gap * RandomFloatRange( 0.85, 1.15 ) );
		fixed = convoy_fixed( def, plan, RandomFloatRange( 0 - TOD_SKY_CONVOY_SIDE, TOD_SKY_CONVOY_SIDE ), RandomFloatRange( 0 - TOD_SKY_CONVOY_DZ, TOD_SKY_CONVOY_DZ ) );
		level thread sortie( localClientNum, def, fixed, tier );
	}
}

// ---- one flight -----------------------------------------------------------------------------------------------------
// tier (v4): 0 = the low layer, 1 = the high layer (the live cap it counts against; the altitude window it plans in).
function sortie( localClientNum, def, fixed, tier )
{
	player = GetLocalPlayer( localClientNum );
	if ( !isdefined( player ) ) return;
	level.tod_sky_serial++;
	serial = level.tod_sky_serial;
	key = live_key( def, tier );
	if ( !ents_free( localClientNum, def.wing_max + 2 ) )                // the wing and up to two rift hosts
	{
		log( "BUDGET n=" + serial + " client=" + localClientNum + " ship=" + def.name + " tier=" + tier_name( tier ) + " ents=" + level.tod_sky_ents[ localClientNum ] + " max=" + TOD_SKY_ENT_MAX );
		return;
	}
	cam = GetCamPosByLocalClientNum( localClientNum );
	plan = flight_plan( def, fixed, player.origin, AnglesToForward( GetCamAnglesByLocalClientNum( localClientNum ) ), cam, tier );
	if ( !isdefined( plan ) )
	{
		log( "NO_LANE client=" + localClientNum + " ship=" + def.name + " tier=" + tier_name( tier ) + " why=" + level.tod_sky_plan_why + " player=" + player.origin );
		return;
	}
	convoy = isdefined( fixed ) && isdefined( fixed.convoy );
	p = plan.p;
	count = RandomIntRange( def.wing_min, def.wing_max + 1 );
	model = def.models[ RandomInt( def.models.size ) ];
	offsets = array( ( 0, 0, 0 ), ( -600, 520, 60 ), ( -600, -520, 60 ), ( -1200, 1040, 120 ), ( -1200, -1040, 120 ) );
	s_in = 0 - plan.approach;
	s_out = p.len + plan.depart;
	s = s_in;
	t = 0;
	if ( plan.worm_in ) t = 0 - TOD_SKY_WORM_OPEN;                       // the rift opens first; the flight starts at the burst
	rin = plan.rin;
	rout = undefined;
	ships = [];
	for ( i = 0; i < count; i++ )
	{
		o = offsets[ i ];
		wp = wing_pose( p, s, 0, o );
		si = stand_in( def, wp[ 0 ], wp[ 1 ], cam );
		ship = spawn( localClientNum, si[ 0 ], "script_model" );
		ship.angles = wp[ 1 ];
		ship SetModel( model );
		ship SetScale( si[ 1 ] );
		ship Hide();
		ship.tod_sky_off = o;
		ship.tod_sky_shown = false;
		ship.tod_sky_k = si[ 1 ];
		ship.tod_sky_te = -1;                                            // time it came out of the arrival rift
		ship.tod_sky_tx = -1;                                            // time it entered the departure rift
		ship.tod_sky_gone = false;
		ship.tod_sky_nzk = [];
		ship.tod_sky_nzb = [];
		ship.tod_sky_nzf = [];
		ship.tod_sky_swaps = 0;
		for ( j = 0; j < def.nozzles.size; j++ )
		{
			ship.tod_sky_nzk[ j ] = "";
			ship.tod_sky_nzb[ j ] = -1;
		}
		if ( !plan.worm_in ) ship.tod_sky_te = 0 - 1000;                  // no rift: it has always been out
		ships[ ships.size ] = ship;
	}
	ents_add( localClientNum, ships.size );
	level.tod_sky_live[ localClientNum ][ key ]++;
	log( "SORTIE n=" + serial + " client=" + localClientNum + " ship=" + def.name + " tier=" + tier_name( tier ) + " model=" + model + " wing=" + count
		+ " lane=" + plan.lane + " relaxed=" + plan.relaxed + " tries=" + plan.tries + " fixed=" + plan.reveal + " convoy=" + convoy + " worm_in=" + plan.worm_in + " worm_out=" + plan.worm_out
		+ " pass_from=" + ( p.a + ( 0, 0, p.z ) ) + " dir=" + p.dir + " len=" + int( p.len ) + " speed=" + p.speed + " approach=" + int( plan.approach )
		+ " depart=" + int( plan.depart ) + " glide=" + p.glide + " climb=" + p.climb + " alt_over_player=" + int( p.z - player.origin[ 2 ] ) + " player=" + player.origin + " cam=" + cam );
	// v4 CONVOYS: a lead that arrives and leaves the normal way may bring followers on its path (never a fixed-path flight
	// itself, never a rift flight: the followers would come out of nothing / fly on past a closed rift) - and only when it
	// is ALONE in its tier, so convoys never pile up past the cap + its followers
	if ( !isdefined( fixed ) && !plan.worm_in && !plan.worm_out && def.convoy_pct > 0 && level.tod_sky_live[ localClientNum ][ key ] <= 1
		&& RandomInt( 100 ) < def.convoy_pct )
		level thread convoy_followers( localClientNum, def, plan, RandomIntRange( def.convoy_min, def.convoy_max + 1 ), tier, serial );
	if ( isdefined( rin ) ) rift_open( localClientNum, rin, serial, "arrival" );

	strobe_ph = RandomFloatRange( 0, TOD_SKY_STROBE_T );
	beacon_ph = RandomFloatRange( 0, TOD_SKY_BEACON_T );
	sounding = false;
	was_full = false;
	hidden_ticks = 0;
	ticks = 0;
	k_min = 1;
	last = GetRealTime();
	t_real = 0;
	flying = true;
	while ( flying )
	{
		dt = rt_step( last );
		last = GetRealTime();
		cam = GetCamPosByLocalClientNum( localClientNum );
		tt = fmax( t, 0 );
		pose = path_pose( p, s, tt );
		ang = pose[ 1 ];
		f = AnglesToForward( ang );
		rt = AnglesToRight( ang );
		up = AnglesToUp( ang );
		strobe_now = fmod( tt + strobe_ph, TOD_SKY_STROBE_T ) < dt;
		strobe_2nd = def.big && fmod( tt + strobe_ph + TOD_SKY_STROBE_T - 0.2, TOD_SKY_STROBE_T ) < dt;   // big ships double-flash
		beacon_now = fmod( tt + beacon_ph, TOD_SKY_BEACON_T ) < dt;
		// THE RIFTS
		if ( isdefined( rin ) )
		{
			rift_follow( rin, cam );
			if ( rin.state == 1 && t >= 0 ) rift_burst( localClientNum, rin, serial );
		}
		if ( plan.worm_out && !isdefined( rout ) && s >= s_out - path_speed( p, s ) * TOD_SKY_WORM_LEAD )
		{
			rout = rift_make( def, path_pose( p, s_out, tt )[ 0 ], cam );
			if ( rout.hidden )
			{
				// a structure would hide the rift: fly out into the distance instead (never vanish big in plain sight)
				log( "WORM_SKIP n=" + serial + " departure rift behind a structure at=" + rout.drawn + ": flies out" );
				rout = undefined;
				plan.worm_out = false;
				s_out = p.len + def.approach;
			}
			else rift_open( localClientNum, rout, serial, "departure" );
		}
		if ( isdefined( rout ) ) rift_follow( rout, cam );
		k_lead = 1;
		all_out = true;
		all_in = true;
		for ( i = 0; i < ships.size; i++ )
		{
			ship = ships[ i ];
			if ( !isdefined( ship ) || ship.tod_sky_gone ) continue;
			along = s + ship.tod_sky_off[ 0 ];
			// emergence from the arrival rift / vanishing into the departure rift
			if ( ship.tod_sky_te < -100 ) e = 1;
			else if ( t >= 0 && along >= s_in )
			{
				if ( ship.tod_sky_te < 0 ) ship.tod_sky_te = t;
				e = smooth( ( t - ship.tod_sky_te ) / TOD_SKY_WORM_GROW );
			}
			else e = 0;
			if ( e < 1 ) all_out = false;
			if ( isdefined( rout ) && along >= s_out )
			{
				if ( ship.tod_sky_tx < 0 )
				{
					ship.tod_sky_tx = t;
					if ( i == 0 ) rift_burst( localClientNum, rout, serial );
				}
				e = e * ( 1 - smooth( ( t - ship.tod_sky_tx ) / TOD_SKY_WORM_SHRINK ) );
				if ( e <= 0.01 )
				{
					ship.tod_sky_gone = true;                                 // inside the rift: nothing left to draw
					engines_off( localClientNum, ship );
					if ( i == 0 && sounding ) { ship StopAllLoopSounds( 0.4 ); sounding = false; }
					ship Hide();
					ship.tod_sky_shown = false;
					continue;
				}
			}
			all_in = false;
			si = stand_in( def, wing_pose( p, s, tt, ship.tod_sky_off )[ 0 ], ang, cam );
			drawn = si[ 0 ];
			k = si[ 1 ] * fmax( e, 0.02 );
			if ( i == 0 ) k_lead = si[ 1 ];
			k_min = fmin( k_min, si[ 1 ] );
			ship MoveTo( drawn, TOD_SKY_TICK * 1.25, 0, 0 );              // keep moving even while hidden
			ship RotateTo( ang, TOD_SKY_TICK * 1.25, 0, 0 );
			if ( abs( k - ship.tod_sky_k ) > 0.0005 )
			{
				ship SetScale( k );
				ship.tod_sky_k = k;
			}
			shown = !si[ 2 ] && e > 0.001;
			if ( !shown )
			{
				if ( ship.tod_sky_shown ) { ship Hide(); ship.tod_sky_shown = false; }
				if ( si[ 2 ] ) hidden_ticks++;
			}
			else
			{
				if ( !ship.tod_sky_shown ) { ship Show(); ship.tod_sky_shown = true; }
				tag_check( def, ship );
				// blinking lights: one-shot flashes at the drawn anchors, at least TOD_SKY_LIGHT_RAD wide on screen
				if ( strobe_now || strobe_2nd || beacon_now )
				{
					rd = Length( drawn - cam );
					foreach ( lt in def.lights )
					{
						kind = lt[ 3 ];
						if ( kind == "s" && !( strobe_now || strobe_2nd ) ) continue;
						if ( kind == "b" && !beacon_now ) continue;
						at = drawn + ( f * lt[ 0 ] - rt * lt[ 1 ] + up * lt[ 2 ] ) * k;
						size = fmax( rd * TOD_SKY_LIGHT_RAD, k * def.light_size );
						PlayFX( localClientNum, light_fx( kind, size ), at );
					}
				}
			}
			engines( localClientNum, def, ship, k, Length( drawn - cam ), shown );
		}
		if ( isdefined( rin ) && rin.state == 2 && all_out && !isdefined( rin.t_done ) ) rin.t_done = t;
		if ( isdefined( rin ) && rin.state == 2 && isdefined( rin.t_done ) && t > rin.t_done + TOD_SKY_WORM_LINGER ) rift_close( localClientNum, rin, serial, t );
		if ( isdefined( rin ) && rin.state == 3 && t > rin.t_close + TOD_SKY_WORM_FADE ) rift_end( localClientNum, rin );
		if ( k_lead >= TOD_SKY_FULL_K && !was_full )
		{
			was_full = true;
			log( "FULL n=" + serial + " ship=" + def.name + " at=" + pose[ 0 ] + " t=" + t );
		}
		if ( isdefined( ships[ 0 ] ) && !ships[ 0 ].tod_sky_gone )
		{
			if ( !sounding && k_lead >= TOD_SKY_SOUND_K && t >= 0 ) { ships[ 0 ] PlayLoopSound( def.loop_alias, 2 ); sounding = true; }
			else if ( sounding && k_lead < TOD_SKY_SOUND_K - 0.1 && s > p.len ) { ships[ 0 ] StopAllLoopSounds( 2 ); sounding = false; }
		}
		// advance on the real clock: far out the ship is fast, near the tower it cruises, out of a rift it surges
		if ( t >= 0 )
		{
			boost = 1;
			if ( plan.worm_in ) boost = worm_boost( t );
			s += path_speed( p, s ) * boost * dt;
		}
		t += dt;
		t_real += dt;
		ticks++;
		if ( isdefined( rout ) )
		{
			if ( all_in && rout.state == 2 ) rift_close( localClientNum, rout, serial, t );
			if ( rout.state == 3 && t > rout.t_close + TOD_SKY_WORM_FADE ) flying = false;
			if ( t_real > 600 ) flying = false;                            // a failsafe: no flight outlives 10 minutes
		}
		else if ( s > s_out ) flying = false;
		wait( TOD_SKY_TICK );
	}

	// GONE: far away and tiny again, or through its rift. Stop everything, delete.
	gone = 0;
	swaps = 0;
	for ( i = 0; i < ships.size; i++ )
	{
		if ( !isdefined( ships[ i ] ) ) continue;
		swaps += ships[ i ].tod_sky_swaps;
		engines_off( localClientNum, ships[ i ] );
		ships[ i ] StopAllLoopSounds( 0.5 );
		ships[ i ] Delete();
		gone++;
	}
	ents_add( localClientNum, 0 - ships.size );                          // every ship spawned is deleted or already gone
	rift_end( localClientNum, rin );
	rift_end( localClientNum, rout );
	level.tod_sky_live[ localClientNum ][ key ]--;
	log( "DONE n=" + serial + " client=" + localClientNum + " ship=" + def.name + " tier=" + tier_name( tier ) + " deleted=" + gone + " secs=" + t_real
		+ " ticks=" + ticks + " rt_ratio=" + ( t_real / fmax( ticks * TOD_SKY_TICK, 0.1 ) ) + " hidden_ticks=" + hidden_ticks
		+ " k_min=" + k_min + " full=" + was_full + " fx_swaps=" + swaps + " tags_scale=" + level.tod_sky_tag_ok
		+ " live=" + level.tod_sky_live[ localClientNum ][ key ] );
}

// ---- ASTEROIDS -----------------------------------------------------------------------------------------------------
// A drift: a great-circle path high in the sky, a size that swells out of the distance and fades back into it, a tumble.
// Pure: the gate flies it. -> struct with the members below, or undefined (no path above the floor elevation).
function rock_plan()
{
	for ( attempt = 0; attempt < 12; attempt++ )
	{
		pl = SpawnStruct();
		yaw = RandomFloatRange( 0, 360 );
		el = RandomFloatRange( TOD_SKY_ROCK_EL_MIN + 12, 76 );
		if ( RandomInt( 100 ) < TOD_SKY_HIGH_PCT ) el = RandomFloatRange( TOD_SKY_HI_BELT_MIN, TOD_SKY_HI_BELT_MAX );   // v4 the high belt
		pl.mid = dir_ye( yaw, el );
		// the path's axis: any direction square to the midpoint
		a = vnorm( vcross( pl.mid, dir_ye( RandomFloatRange( 0, 360 ), RandomFloatRange( -60, 60 ) ) ) );
		pl.axis = a;
		pl.across = vcross( a, pl.mid );                                  // the direction of travel at the midpoint
		pl.w = RandomFloatRange( 0.35, 1.1 );                              // degrees per second
		pl.secs = RandomFloatRange( 55, 130 );
		d0 = rock_dir( pl, 0 );
		d1 = rock_dir( pl, pl.secs );
		if ( d0[ 2 ] < Sin( TOD_SKY_ROCK_EL_MIN ) || d1[ 2 ] < Sin( TOD_SKY_ROCK_EL_MIN ) ) continue;
		pl.cluster = RandomInt( 100 ) < 30;
		n = 1;
		if ( pl.cluster ) n = RandomIntRange( 2, 5 );
		big = RandomFloatRange( 0.35, 1.0 );
		if ( RandomInt( 100 ) < 6 ) big = RandomFloatRange( 1.2, 1.9 );    // now and then one passes close
		if ( pl.cluster ) big = RandomFloatRange( 0.3, 0.75 );
		pl.rocks = [];
		for ( j = 0; j < n; j++ )
		{
			r = SpawnStruct();
			r.pick = rock_pick();
			r.ang = big * RandomFloatRange( 0.55, 1.0 );                   // the peak angular size, degrees
			if ( j == 0 ) r.ang = big;
			r.oa = 0;
			r.oc = 0;
			if ( j > 0 )
			{
				r.oa = RandomFloatRange( -3.5, 3.5 ) * big * 0.01745;        // along / across offsets (radians)
				r.oc = RandomFloatRange( -2.5, 2.5 ) * big * 0.01745;
			}
			r.a0 = ( RandomFloatRange( 0, 360 ), RandomFloatRange( 0, 360 ), RandomFloatRange( 0, 360 ) );
			r.spin = ( RandomFloatRange( -16, 16 ), RandomFloatRange( -16, 16 ), RandomFloatRange( -16, 16 ) );
			pl.rocks[ j ] = r;
		}
		return pl;
	}
	return undefined;
}

// which rock model (weights: boulder 30, shard 22, veined 13, slab 15, rubble 20) -> index into level.tod_sky_rocks
function rock_pick()
{
	roll = RandomInt( 100 );
	acc = 0;
	for ( i = 0; i < level.tod_sky_rocks.size; i++ )
	{
		acc += level.tod_sky_rocks[ i ][ 3 ];
		if ( roll < acc ) return i;
	}
	return 0;
}

function rock_dir( pl, t )
{
	th = pl.w * ( t - pl.secs * 0.5 );
	return pl.mid * Cos( th ) + pl.across * Sin( th );
}

// The rock's angular size (degrees) at time t: a flyby (1 / sqrt(1 + x^2)) under an envelope that grows from and fades
// to nothing at the ends, so it is never popped in or out.
function rock_ang( pl, r, t )
{
	x = ( t - pl.secs * 0.5 ) / ( pl.secs * 0.3 );
	env = smooth( fmin( t, pl.secs - t ) / ( pl.secs * 0.18 ) );
	return r.ang * env / Sqrt( 1 + x * x );
}

// -> array( virtual origin, angles, angular size in radians ) for rock r of drift pl at time t, seen from cam.
function rock_state( pl, r, t, cam )
{
	// Native CSC locals are case-insensitive: direction and distance must not be d/D.
	direction = rock_dir( pl, t );
	if ( r.oa != 0 || r.oc != 0 ) direction = vnorm( direction + vcross( pl.axis, direction ) * r.oa + pl.axis * r.oc );
	ang = rock_ang( pl, r, t ) * 0.017453;
	rad = level.tod_sky_rocks[ r.pick ][ 1 ];
	distance = 2 * rad / fmax( ang, 0.00001 );
	angles = r.a0 + r.spin * t;
	return array( cam + direction * distance, ( fmod( angles[ 0 ] + 3600, 360 ), fmod( angles[ 1 ] + 3600, 360 ), fmod( angles[ 2 ] + 3600, 360 ) ), ang );
}

function rock_loop( localClientNum )
{
	level endon( "tod_sky_stop" );
	waitrealtime( RandomFloatRange( 3, 8 ) );
	while ( true )
	{
		if ( level.tod_sky_rocks_live[ localClientNum ] < TOD_SKY_ROCKS_MAX && level.tod_sky_rocks.size )
			level thread drift( localClientNum );
		waitrealtime( RandomFloatRange( TOD_SKY_ROCK_GAP_MIN, TOD_SKY_ROCK_GAP_MAX ) );
	}
}

function rock_model( pick )
{
	models = level.tod_sky_rocks[ pick ][ 0 ];
	return models[ RandomInt( models.size ) ];
}

function drift( localClientNum )
{
	pl = rock_plan();
	if ( !isdefined( pl ) ) return;
	level.tod_sky_serial++;
	serial = level.tod_sky_serial;
	if ( !ents_free( localClientNum, pl.rocks.size ) )
	{
		log( "BUDGET n=" + serial + " client=" + localClientNum + " rocks=" + pl.rocks.size + " ents=" + level.tod_sky_ents[ localClientNum ] + " max=" + TOD_SKY_ENT_MAX );
		return;
	}
	cam = GetCamPosByLocalClientNum( localClientNum );
	models = [];
	for ( j = 0; j < pl.rocks.size; j++ )
	{
		r = pl.rocks[ j ];
		r.bdef = ball_def( level.tod_sky_rocks[ r.pick ][ 1 ] );
		st = rock_state( pl, r, 0, cam );
		si = stand_in( r.bdef, st[ 0 ], st[ 1 ], cam );
		m = spawn( localClientNum, si[ 0 ], "script_model" );
		m SetModel( rock_model( r.pick ) );
		m.angles = st[ 1 ];
		m SetScale( si[ 1 ] );
		m Hide();
		m.tod_sky_shown = false;
		m.tod_sky_k = si[ 1 ];
		models[ j ] = m;
	}
	ents_add( localClientNum, models.size );
	level.tod_sky_rocks_live[ localClientNum ]++;
	log( "ROCK n=" + serial + " client=" + localClientNum + " count=" + pl.rocks.size + " rock=" + pl.rocks[ 0 ].pick + " peak_deg=" + pl.rocks[ 0 ].ang
		+ " deg_per_s=" + pl.w + " secs=" + pl.secs + " mid=" + pl.mid );
	t = 0;
	last = GetRealTime();
	shown_ticks = 0;
	while ( t < pl.secs )
	{
		dt = rt_step( last );
		last = GetRealTime();
		cam = GetCamPosByLocalClientNum( localClientNum );
		for ( j = 0; j < pl.rocks.size; j++ )
		{
			r = pl.rocks[ j ];
			m = models[ j ];
			st = rock_state( pl, r, t, cam );
			si = stand_in( r.bdef, st[ 0 ], st[ 1 ], cam );
			m MoveTo( si[ 0 ], TOD_SKY_TICK * 1.25, 0, 0 );
			m RotateTo( st[ 1 ], TOD_SKY_TICK * 1.25, 0, 0 );
			if ( abs( si[ 1 ] - m.tod_sky_k ) > 0.00002 )
			{
				m SetScale( si[ 1 ] );
				m.tod_sky_k = si[ 1 ];
			}
			vis = !si[ 2 ] && st[ 2 ] > TOD_SKY_ROCK_MIN_RAD;
			if ( vis && !m.tod_sky_shown ) { m Show(); m.tod_sky_shown = true; }
			else if ( !vis && m.tod_sky_shown ) { m Hide(); m.tod_sky_shown = false; }
			if ( vis && j == 0 ) shown_ticks++;
		}
		t += dt;
		wait( TOD_SKY_TICK );
	}
	for ( j = 0; j < models.size; j++ )
		if ( isdefined( models[ j ] ) ) models[ j ] Delete();
	ents_add( localClientNum, 0 - models.size );
	level.tod_sky_rocks_live[ localClientNum ]--;
	log( "ROCK_DONE n=" + serial + " shown_ticks=" + shown_ticks + " live=" + level.tod_sky_rocks_live[ localClientNum ] );
}

// ---- rocks round the black holes -------------------------------------------------------------------------------------
// hole = array( centre dir, shadow radius deg, disc axis e1, disc axis e2, rocks, spin sign ) from tod_sky_lanes::holes():
// a rock orbits in the painted disc's plane at rho x the shadow radius, spirals in, hides behind the shadow on the far
// side, and is swallowed with a flash at the horizon.
function hole_rock( hole, t0 )
{
	o = SpawnStruct();
	o.rho0 = RandomFloatRange( 2.2, 4.0 );
	o.phi = RandomFloatRange( 0, 360 );
	o.secs = RandomFloatRange( 70, 150 );
	o.w0 = RandomFloatRange( 2.2, 3.6 ) * hole[ 5 ];                     // degrees of orbit per second at rho0
	o.pick = rock_pick();
	o.bdef = ball_def( level.tod_sky_rocks[ o.pick ][ 1 ] );            // v4: once per rock, not once per tick
	o.ang = fmax( hole[ 1 ] * RandomFloatRange( 0.05, 0.09 ), 0.12 );   // angular size, degrees
	o.a0 = ( RandomFloatRange( 0, 360 ), RandomFloatRange( 0, 360 ), RandomFloatRange( 0, 360 ) );
	o.spin = ( RandomFloatRange( -20, 20 ), RandomFloatRange( -20, 20 ), RandomFloatRange( -20, 20 ) );
	o.t = t0;
	o.age = 0;                                                          // since it came into sight (it fades in)
	return o;
}

function hole_rho( o )
{
	u = fclamp( o.t / o.secs, 0, 1 );
	return o.rho0 - ( o.rho0 - 1.0 ) * u * Sqrt( u );                   // accelerating inward
}

// -> array( direction, far side, angular size (radians), angles ) for an orbiting rock.
function hole_state( hole, o )
{
	rho = hole_rho( o );
	tr = Sin( hole[ 1 ] ) / Cos( hole[ 1 ] );
	off = ( hole[ 2 ] * Cos( o.phi ) + hole[ 3 ] * Sin( o.phi ) ) * ( rho * tr );
	d = vnorm( hole[ 0 ] + off );
	far = vdot( off, hole[ 0 ] ) > 0;
	grow = smooth( o.age / 4.0 );                                        // it fades in out of the disc's glow, wherever it starts
	angles = o.a0 + o.spin * o.t;
	return array( d, far, o.ang * 0.017453 * grow, ( fmod( angles[ 0 ] + 3600, 360 ), fmod( angles[ 1 ] + 3600, 360 ), fmod( angles[ 2 ] + 3600, 360 ) ) );
}

function hole_loop( localClientNum, hole )
{
	level endon( "tod_sky_stop" );
	waitrealtime( RandomFloatRange( 2, 6 ) );
	orbit = [];
	models = [];
	for ( i = 0; i < hole[ 4 ]; i++ )
	{
		orbit[ i ] = hole_rock( hole, RandomFloatRange( 0, 60 ) );
		models[ i ] = undefined;
	}
	last = GetRealTime();
	eaten = 0;
	while ( true )
	{
		dt = rt_step( last );
		last = GetRealTime();
		cam = GetCamPosByLocalClientNum( localClientNum );
		for ( i = 0; i < orbit.size; i++ )
		{
			o = orbit[ i ];
			rho = hole_rho( o );
			o.phi += o.w0 * Sqrt( ( o.rho0 * o.rho0 * o.rho0 ) / ( rho * rho * rho ) ) * dt;
			o.t += dt;
			o.age += dt;
			st = hole_state( hole, o );
			rad = level.tod_sky_rocks[ o.pick ][ 1 ];
			D = 2 * rad / fmax( st[ 2 ], 0.00001 );
			si = stand_in( o.bdef, cam + st[ 0 ] * D, st[ 3 ], cam );
			if ( !isdefined( models[ i ] ) )
			{
				models[ i ] = spawn( localClientNum, si[ 0 ], "script_model" );
				ents_add( localClientNum, 1 );
				models[ i ] SetModel( rock_model( o.pick ) );
				models[ i ] Hide();
				models[ i ].tod_sky_shown = false;
				models[ i ].tod_sky_k = 0;
			}
			m = models[ i ];
			m MoveTo( si[ 0 ], TOD_SKY_TICK * 1.25, 0, 0 );
			m RotateTo( st[ 3 ], TOD_SKY_TICK * 1.25, 0, 0 );
			if ( abs( si[ 1 ] - m.tod_sky_k ) > 0.00002 )
			{
				m SetScale( si[ 1 ] );
				m.tod_sky_k = si[ 1 ];
			}
			// behind the shadow: the black hole hides it
			behind = st[ 1 ] && vdot( st[ 0 ], hole[ 0 ] ) > Cos( hole[ 1 ] );
			vis = !si[ 2 ] && !behind && st[ 2 ] > TOD_SKY_ROCK_MIN_RAD;
			if ( vis && !m.tod_sky_shown ) { m Show(); m.tod_sky_shown = true; }
			else if ( !vis && m.tod_sky_shown ) { m Hide(); m.tod_sky_shown = false; }
			if ( o.t >= o.secs )
			{
				// swallowed at the horizon: a flash (only if it was in sight), then a new rock comes in from the disc
				if ( m.tod_sky_shown )
					PlayFX( localClientNum, light_fx( "s", Length( si[ 0 ] - cam ) * TOD_SKY_LIGHT_RAD * 1.6 ), si[ 0 ] );
				eaten++;
				log( "HOLE_EAT client=" + localClientNum + " hole=" + hole[ 6 ] + " rock=" + o.pick + " seen=" + m.tod_sky_shown + " eaten=" + eaten );
				m Delete();
				ents_add( localClientNum, -1 );
				models[ i ] = undefined;
				orbit[ i ] = hole_rock( hole, 0 );
			}
		}
		wait( TOD_SKY_TICK );
	}
}

// ---- SHOOTING STARS + FIREBALLS -----------------------------------------------------------------------------------
// The farthest point along dir from the camera that stays `margin` inside the sealed volume.
function box_reach( cam, dir, margin )
{
	r = 1000000;
	lo = level.tod_sky_lo + ( margin, margin, margin );
	hi = level.tod_sky_hi - ( margin, margin, margin );
	for ( j = 0; j < 3; j++ )
	{
		if ( dir[ j ] > 0.000001 ) r = fmin( r, ( hi[ j ] - cam[ j ] ) / dir[ j ] );
		else if ( dir[ j ] < -0.000001 ) r = fmin( r, ( lo[ j ] - cam[ j ] ) / dir[ j ] );
	}
	return r;
}

function in_blocker( p )
{
	foreach ( b in level.tod_sky_blockers )
	{
		if ( p[ 0 ] < b[ 0 ][ 0 ] || p[ 0 ] > b[ 1 ][ 0 ] ) continue;
		if ( p[ 1 ] < b[ 0 ][ 1 ] || p[ 1 ] > b[ 1 ][ 1 ] ) continue;
		if ( p[ 2 ] < b[ 0 ][ 2 ] || p[ 2 ] > b[ 1 ][ 2 ] ) continue;
		return true;
	}
	return false;
}

// A streak: -> array( start, direction, length ) inside the sealed volume and clear of every structure near its walls,
// high in the sky and falling across it, or undefined. radiant (optional) = a shower's shared start direction.
function star_plan( cam, speed, secs, el_min, el_max, radiant )
{
	L = speed * secs;
	for ( attempt = 0; attempt < 14; attempt++ )
	{
		if ( isdefined( radiant ) ) d0 = vnorm( radiant + ( RandomFloatRange( -0.12, 0.12 ), RandomFloatRange( -0.12, 0.12 ), RandomFloatRange( -0.08, 0.08 ) ) );
		else d0 = dir_ye( RandomFloatRange( 0, 360 ), RandomFloatRange( el_min, el_max ) );
		r = fmin( box_reach( cam, d0, 400 ), TOD_SKY_STAR_R_MAX );
		if ( r < TOD_SKY_STAR_R_MIN ) continue;
		p0 = cam + d0 * ( r * 0.95 );
		right = vnorm( vcross( d0, ( 0, 0, 1 ) ) );
		upv = vcross( right, d0 );
		psi = RandomFloatRange( 200, 340 );                                 // mostly falling, left or right
		dir = right * Cos( psi ) + upv * Sin( psi );
		p1 = p0 + dir * L;
		if ( box_reach( p0, dir, 300 ) < L ) continue;
		pm = p0 + dir * ( L * 0.5 );
		if ( in_blocker( p0 ) || in_blocker( pm ) || in_blocker( p1 ) ) continue;
		e1 = vnorm( p1 - cam );
		if ( e1[ 2 ] < Sin( 12 ) ) continue;                                  // it stays above the skyline
		return array( p0, dir, L );
	}
	return undefined;
}

function star_one( localClientNum, radiant, tag )
{
	v = 0;
	roll = RandomInt( 100 );
	if ( roll >= 50 ) v = 1;
	if ( roll >= 85 ) v = 2;
	speed = tod_sky_lanes::star_speed( v );
	secs = tod_sky_lanes::star_secs( v );
	cam = GetCamPosByLocalClientNum( localClientNum );
	el_lo = 25;
	el_hi = 74;
	if ( !isdefined( radiant ) && RandomInt( 100 ) < TOD_SKY_HIGH_PCT )                                  // v4 the high belt
	{
		el_lo = TOD_SKY_HI_BELT_MIN;
		el_hi = TOD_SKY_HI_BELT_MAX;
	}
	pl = star_plan( cam, speed, secs, el_lo, el_hi, radiant );
	if ( !isdefined( pl ) ) return undefined;
	PlayFX( localClientNum, star_fx( v ), pl[ 0 ], pl[ 1 ] );
	rd = Length( pl[ 0 ] - cam );
	log( tag + " client=" + localClientNum + " variant=" + v + " at=" + pl[ 0 ] + " dir=" + pl[ 1 ] + " arc_deg=" + ( 57.3 * pl[ 2 ] / fmax( rd, 1 ) ) + " dist=" + rd );
	return pl;
}

function star_loop( localClientNum )
{
	level endon( "tod_sky_stop" );
	waitrealtime( RandomFloatRange( 4, 12 ) );
	while ( true )
	{
		if ( RandomInt( 100 ) < TOD_SKY_SHOWER_PCT )
		{
			// a shower: 4..7 streaks from one radiant within ~3 s
			radiant = dir_ye( RandomFloatRange( 0, 360 ), RandomFloatRange( 40, 78 ) );
			n = RandomIntRange( 4, 8 );
			log( "SHOWER client=" + localClientNum + " count=" + n + " radiant=" + radiant );
			for ( i = 0; i < n; i++ )
			{
				star_one( localClientNum, radiant, "STAR shower" );
				waitrealtime( RandomFloatRange( 0.15, 0.7 ) );
			}
		}
		else star_one( localClientNum, undefined, "STAR" );
		waitrealtime( RandomFloatRange( TOD_SKY_STAR_GAP_MIN, TOD_SKY_STAR_GAP_MAX ) );
	}
}

function fireball_loop( localClientNum )
{
	level endon( "tod_sky_stop" );
	waitrealtime( RandomFloatRange( 40, 90 ) );
	while ( true )
	{
		green = RandomInt( 100 ) < 30;
		cam = GetCamPosByLocalClientNum( localClientNum );
		pl = star_plan( cam, tod_sky_lanes::ball_speed(), tod_sky_lanes::ball_secs(), 18, 48, undefined );
		if ( isdefined( pl ) )
		{
			PlayFX( localClientNum, ball_fx( green ), pl[ 0 ], pl[ 1 ] );
			log( "FIREBALL client=" + localClientNum + " green=" + green + " at=" + pl[ 0 ] + " dir=" + pl[ 1 ] + " dist=" + Length( pl[ 0 ] - cam ) );
		}
		waitrealtime( RandomFloatRange( TOD_SKY_BALL_GAP_MIN, TOD_SKY_BALL_GAP_MAX ) );
	}
}

// ---- SATELLITES (v4) -------------------------------------------------------------------------------------------------
// A slow steady point of light crossing the upper sky on a great circle (a rock's drift, but a point: it never swells),
// tumbling: a small flare every few seconds. Pure plan: the gate flies it.
function sat_plan()
{
	for ( attempt = 0; attempt < 12; attempt++ )
	{
		pl = SpawnStruct();
		pl.mid = dir_ye( RandomFloatRange( 0, 360 ), RandomFloatRange( TOD_SKY_SAT_EL_MIN + 20, 88 ) );
		a = vnorm( vcross( pl.mid, dir_ye( RandomFloatRange( 0, 360 ), RandomFloatRange( -60, 60 ) ) ) );
		pl.axis = a;
		pl.across = vcross( a, pl.mid );
		pl.w = RandomFloatRange( 0.2, 0.5 );                                 // degrees per second
		pl.secs = RandomFloatRange( 70, 160 );
		d0 = rock_dir( pl, 0 );
		d1 = rock_dir( pl, pl.secs );
		if ( d0[ 2 ] < Sin( TOD_SKY_SAT_EL_MIN ) || d1[ 2 ] < Sin( TOD_SKY_SAT_EL_MIN ) ) continue;
		pl.flare_t = RandomFloatRange( 2.2, 4.5 );                           // its tumble: one flare every ... s
		return pl;
	}
	return undefined;
}

// -> array( drawn point, scale, hidden ) for the satellite of plan pl at time t: a point far along its direction, pressed
// to the sealed box like every stand-in.
function sat_point( pl, t, cam )
{
	return stand_in( level.tod_sky_sat_def, cam + rock_dir( pl, t ) * 200000, ( 0, 0, 0 ), cam );
}

// a satellite's point in four sizes (gen_fx.py SATS 18 / 48 / 110 / 250 units; the thresholds are their geometric means)
function sat_fx( size )
{
	if ( size < 29.4 ) return "tod/sky/fx_sky_sat_xs";
	if ( size < 72.7 ) return "tod/sky/fx_sky_sat_s";
	if ( size < 166 ) return "tod/sky/fx_sky_sat_m";
	return "tod/sky/fx_sky_sat_l";
}

function satellite_loop( localClientNum )
{
	level endon( "tod_sky_stop" );
	waitrealtime( RandomFloatRange( 6, 20 ) );
	while ( true )
	{
		if ( level.tod_sky_sats_live[ localClientNum ] < TOD_SKY_SATS_MAX )
			level thread satellite( localClientNum );
		waitrealtime( RandomFloatRange( TOD_SKY_SAT_GAP_MIN, TOD_SKY_SAT_GAP_MAX ) );
	}
}

function satellite( localClientNum )
{
	pl = sat_plan();
	if ( !isdefined( pl ) ) return;
	level.tod_sky_serial++;
	serial = level.tod_sky_serial;
	if ( !ents_free( localClientNum, 1 ) )
	{
		log( "BUDGET n=" + serial + " client=" + localClientNum + " satellite ents=" + level.tod_sky_ents[ localClientNum ] + " max=" + TOD_SKY_ENT_MAX );
		return;
	}
	cam = GetCamPosByLocalClientNum( localClientNum );
	si = sat_point( pl, 0, cam );
	host = spawn( localClientNum, si[ 0 ], "script_model" );
	ents_add( localClientNum, 1 );
	host SetModel( "tag_origin" );
	level.tod_sky_sats_live[ localClientNum ]++;
	log( "SAT n=" + serial + " client=" + localClientNum + " deg_per_s=" + pl.w + " secs=" + pl.secs + " mid=" + pl.mid + " flare_t=" + pl.flare_t );
	host util::waittill_dobj( localClientNum );
	fx = undefined;
	fxname = "";
	t = 0;
	last = GetRealTime();
	next_flare = pl.flare_t;
	shown_ticks = 0;
	flares = 0;
	while ( isdefined( host ) && t < pl.secs )
	{
		dt = rt_step( last );
		last = GetRealTime();
		cam = GetCamPosByLocalClientNum( localClientNum );
		si = sat_point( pl, t, cam );
		host MoveTo( si[ 0 ], TOD_SKY_TICK * 1.25, 0, 0 );
		rd = Length( si[ 0 ] - cam );
		want = "";
		if ( !si[ 2 ] ) want = sat_fx( rd * TOD_SKY_SAT_RAD );             // a structure in the way: dark until it is past
		if ( want != fxname )
		{
			if ( isdefined( fx ) ) StopFX( localClientNum, fx );
			fx = undefined;
			fxname = want;
			if ( want != "" ) fx = PlayFXOnTag( localClientNum, want, host, "tag_origin" );
		}
		if ( want != "" )
		{
			shown_ticks++;
			if ( t >= next_flare )
			{
				PlayFX( localClientNum, light_fx( "s", rd * TOD_SKY_SAT_RAD * TOD_SKY_SAT_FLARE ), si[ 0 ] );
				flares++;
			}
		}
		if ( t >= next_flare ) next_flare += pl.flare_t;
		t += dt;
		wait( TOD_SKY_TICK );
	}
	if ( isdefined( fx ) ) StopFX( localClientNum, fx );
	if ( isdefined( host ) ) host Delete();
	ents_add( localClientNum, -1 );
	level.tod_sky_sats_live[ localClientNum ]--;
	log( "SAT_DONE n=" + serial + " client=" + localClientNum + " shown_ticks=" + shown_ticks + " flares=" + flares + " live=" + level.tod_sky_sats_live[ localClientNum ] );
}

// ---- session 61's first-jump scene -----------------------------------------------------------------------------
// tod_jump_title_ignite reaches the flyer's client as the sign blazes (t 4.8, the impact at 4.6); the white veil lifts
// 6.2..7.4 and the camera holds on the sign to 10.3 (session 61/7f, test_jump_title.js). The salute waits SALUTE_DELAY
// (real time) and sends a fighter wing across the blazing sign from outside the frame (it crosses at ~8.8), and a hauler
// starts its far approach toward the tower. Once per local client per match.
function reveal_watch()
{
	level endon( "tod_sky_stop" );
	while ( true )
	{
		level waittill( "tod_jump_title_ignite", localClientNum );
		if ( !isdefined( localClientNum ) ) localClientNum = 0;
		if ( IS_TRUE( level.tod_sky_revealed[ localClientNum ] ) ) continue;
		if ( !isdefined( level.tod_sky_live[ localClientNum ] ) ) continue;
		level.tod_sky_revealed[ localClientNum ] = true;
		level thread reveal( localClientNum );
	}
}

function reveal( localClientNum )
{
	waitrealtime( TOD_SKY_SALUTE_DELAY );
	log( "REVEAL client=" + localClientNum + " delay=" + TOD_SKY_SALUTE_DELAY );
	high = tod_sky_lanes::reveal_high();
	low = tod_sky_lanes::reveal_low();
	level thread sortie( localClientNum, level.tod_sky_classes[ high.ship ], high, 0 );
	level thread sortie( localClientNum, level.tod_sky_classes[ low.ship ], low, 0 );
}

function log( msg )
{
	if ( !TOD_SKY_LOG ) return;
	line = "[TOD_SKY] ms=" + GetRealTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
