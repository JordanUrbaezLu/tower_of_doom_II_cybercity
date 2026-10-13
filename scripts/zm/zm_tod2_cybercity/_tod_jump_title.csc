// =============================================================================
// _tod_jump_title.csc - THE FIRST JUMP'S CRASH (docs/196 §4, §6), the client half.
//
// User 2026-09-29: "the skybox sign is like dimmed then there are two of the spaceships going at each other
// during the cinematic scene they crash into each other they do a huge explosion so you can't see anything and
// then behind is actually the tower of doom sign all lit up completely bright ... reuse their spaceships ...
// sounds and huge explosion effect". After the first play: "The kaboom ended early ... make sure sign doesnt
// light up until explosion happens ... double check all your work" and "if we need the jump to last longer. You
// can do that as well". 2026-09-30, the review: "the thing i really want is the sign to not glow and actually
// be very dull and then after explosion it should glow very bright".
//
// THE SIGN, FOURTH PASS (rev 5, docs/196 §6). The sky's sign is BAKED DULL now (build_city.py --sign-state
// dull: unlit tubes, dark metal), so it is very dull from the match's first frame, through the crown hall's
// window, on the balcony and through the standoff - nothing has to hide it (the seven-puff smoke veil of rev 3
// is RETIRED). The LIT sign is a CARD MODEL (tod_jt_sign_lit, tools/jump_title/make_sign_card.py: the same
// painting, the same card geometry as the sky's, an HDR emissive material) that this client spawns hidden at
// the scene's start on the sign's bearing, TOD_JT_SIGN_DIST out, and moves with the camera every frame, so it
// sits exactly over the dull bake. At THE REVEAL it FLICKERS ON like a neon sign taking power (flicker_ms(),
// the power surge under it), holds, and STAYS ON for the rest of the match on this client (the card is never
// deleted by a scene: level.tod_jt_lit[client]). The blaze glows surge over it once it holds.
//
// CLIENT ONLY, on the FLYER's own game (session 9c's sky-fleet rule: zero server entities). _tod_jumppad.gsc
// owns the camera, the white flash (TodJumpCine.lua), the shake and the rumble, and sends the beats with
// util::clientNotify on the jumper only, so they arrive here as `level waittill( <beat>, localClientNum )`
// (seconds from the launch of an 11.6 s first flight; the fifth pass tightened every gap):
//   tod_jump_title_start   t=0.0  the lit card loads HIDDEN on the sign's bearing (the sky's sign is dull by
//                                 itself). Two of 9c's gunships are loaded HIDDEN at their standoff spots, and
//                                 as the camera turns to the sign they WARP IN (a portal flash, a bamf panned
//                                 from the ship): the magenta one on the left at 1.3 s, the green one on the
//                                 right at 1.95 s, bows facing, engines idling, hovering. Nothing pops in.
//   tod_jump_title_ships   t=2.5  THE CHARGE: after 0.6 s of standoff both engines flare and they RAM each other
//                                 (TOD_JT_RUN_SECS, all acceleration)
//   tod_jump_title_impact  t=3.6  THE CRASH: the boom and its rumble; under the quarter second of FULL white
//                                 (TOD_JT_UNDER_WHITE) the hulls are gone; the white burns out onto a fireball
//                                 that fills the frame and burns ~2.5 s; two reactor blasts a beat apart, the
//                                 burning wreckage falling to the city
//   tod_jump_title_ignite  t=3.8  behind the full white: nothing visible changes yet (the sign stays dull under
//                                 the fire); this beat arms THE REVEAL on this client's real clock. Session 9c's
//                                 salute listens on this beat. A scene cut short AFTER this beat lights the
//                                 sign at once (no show, but never a dull sign after the crash).
//                          +0.7   THE REVEAL (TOD_JT_REVEAL): as the white burns out onto the fire, the power surge is heard and the
//                                 sign FLICKERS ON (flicker_ms: on/off/on/off/on/off, then steady), the blaze
//                                 glows ramp up over the held card, the crest's ring and its eyes flare, sparks
//                                 rain off the letters (gen_fx.py lays the glows out against these beats)
//   tod_jump_title_end     t=8.4  the camera swings back to the tower: the glows fade as the sign leaves the
//                                 frame; the lit card stays. Also sent AT ONCE on every cut-short scene (a card
//                                 deal, death, the flight over), which drops the ships and the effects at once.
// Every beat is handled ONCE per scene (a repeat is ignored); a WATCHDOG clears everything if the _end never
// arrives; a new _start replaces an old scene cleanly.
//
// THE CLOCK (the first play, 2026-09-29): a CLIENT `wait` is NOT real time here - it counts frames, and on the
// user's ~165 fps machine `wait 14` ended after 5.1 real seconds (the watchdog cut the explosion 1.2 s after the
// impact) and `wait 1.5` after 0.55 (the warps fired before the turn). A MoveTo rides the same script clock. So
// every delay here is `waitrealtime` (stock's own real-time wait, util::server_wait) and every motion is set each
// frame from GetRealTime (the ships' hover and ram). test_jump_title.js fails on a plain `wait <seconds>` or a
// MoveTo in this file. CLOCK in the log compares the two clocks once per scene.
//
// TWO KINDS OF PLACE. The ships, the crash and the wreckage are fixed in the WORLD (the explosion has real
// depth): 6,000 u due west of the rider at the impact, in front of the title, a shallow X across the frame. The
// lit card and the blaze belong to the SKY sign, which is at infinity: they ride a bearing from the camera
// (camera + the sign's bearing x TOD_JT_SIGN_DIST, moved every frame), so they never slide across the letters
// as the rider flies (tools/jump_title/gen_fx.py lays the glows' offsets out as angles at that distance;
// make_sign_card.py sizes the card by the sky's own GATE geometry at it). TOD_JT_SIGN_DIST sits BEHIND both
// gunships and the crash (the farthest hull point on the card's extent is ~8,700 u) and keeps the card's corners
// inside the sealed sky volume. The sky puts the sign at yaw -(the SSIs' sun azimuth + skyRotation) - roll
// (docs/196 §3, measured in game; test_jumppad).
// tools/jump_title/test_jump_title.js proves the scene against the live sources: the crash centred at the impact
// on every take-off x landing, each ship in frame at its warp, both bows in frame at the standoff, every ship
// corner inside the sealed sky volume and >= 1,500 u from every brush and keep-out (9c's rule), the host and the
// card inside the volume, the beats one per frame, the hull removal inside the full white, the card shown only
// at the reveal, the flicker's length, the glows on the held card, the clocks.
//
// Dev logs: [TOD_JT] INIT / START / CLOCK / WARP / CHARGE / IMPACT / IGNITE / REVEAL / LIT / END / CLEANUP /
// WATCHDOG (TOD_JT_LOG; zero it before a publish).
// =============================================================================

#using scripts\shared\callbacks_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;

#insert scripts\shared\shared.gsh;

#precache( "client_fx", "tod/sky/fx_sky_eng_gunship" );   // session 9c's engine glow + contrail (the fleet's own)
#precache( "client_fx", "tod/jump/fx_jt_warp" );
#precache( "client_fx", "tod/jump/fx_jt_burn" );
#precache( "client_fx", "tod/jump/fx_jt_boom" );
#precache( "client_fx", "tod/jump/fx_jt_blast" );
#precache( "client_fx", "tod/jump/fx_jt_wreck" );
#precache( "client_fx", "tod/jump/fx_jt_blaze" );

#namespace tod_jump_title;

#define TOD_JT_LOG        1         // [TOD_JT] records (dev-block output; the user's launcher enables it); 0 before a publish
#define TOD_JT_REV        7         // 7: the sign lit 0.7 s after the ignite, the hold 0.5 s longer (end beat 8.4, 2026-10-01);
                                    // 6: the fifth pass's pacing (a 1.1 s ram, the sign lit 1.0 s after the ignite); 5: the sign
                                    // baked DULL, the LIT sign a card that flickers on at the reveal and stays
                                    // (2026-09-30); 4: the sounds' second pass; 3: the real clock, the retimed crash
// THE PLACE (docs/196 §4). test_jump_title.js re-proves every number here against the live sources.
#define TOD_JT_CRASH      ( -5879, 3390, 23190 )
#define TOD_JT_DIVE       12        // the approach line's slope (deg): A runs north and down, B south and up
#define TOD_JT_BOW        1620      // tag_origin -> the bow tip (art/sky_ships/manifest.json, gunship bounds x max)
#define TOD_JT_RUN        2900      // each ship's run, standoff -> contact
#define TOD_JT_RUN_SECS   1.1       // LOCKSTEP: _tod_jumppad.gsc TOD_JUMPPAD_CINE_IMPACT_AT - _SHIPS_AT (1.2 until the fifth pass)
#define TOD_JT_RUN_ACCEL  0.85      // the run is all acceleration: this share of it speeding up (scene_geometry trapezoid)
#define TOD_JT_BOB        60        // the standoff's idle hover (up and down, units)
#define TOD_JT_BOB_SECS   2.2       // ... one full bob
#define TOD_JT_WARP_A     1.3       // s after the start: the magenta ship warps in (it enters a 65-deg frame first; 1.5 until the fifth pass)
#define TOD_JT_WARP_B     1.95      // ... and the green one, as the turn brings its side of the sign into frame (2.25 until the fifth pass)
#define TOD_JT_UNDER_WHITE 0.12     // s after the impact: the hulls go (the white is FULL from 0.06 to 0.31 s,
                                    // TodJumpCine FLASH_IN_MS / FLASH_HOLD_MS)
#define TOD_JT_REVEAL     0.7       // s after the ignite: the sign flickers on, 0.9 s after the impact as the white burns out onto the
                                    // fireball (2.2 until the fifth pass; the user: "taking a little bit too long to light up"; 1.0 until
                                    // 2026-10-01: "the lights on the sign should start about 300ms earlier"); LOCKSTEP gen_fx.py REVEAL
#define TOD_JT_WRECK_A    ( -5879, 1805, 23527 )    // each hull's centre at the contact: its reactor blast + falling wreckage
#define TOD_JT_WRECK_B    ( -5879, 4975, 22853 )
// THE SKY SIGN (at infinity): the card and the glows' host ride its bearing from the camera.
#define TOD_JT_SIGN_YAW   180       // LOCKSTEP: _tod_jumppad.gsc TOD_JUMPPAD_CINE_SIGN_YAW (the sky's sign bearing)
#define TOD_JT_SIGN_EL    11        // LOCKSTEP: tools/sky3d/build_city.py GATE box_el (the text box centre's elevation)
#define TOD_JT_SIGN_DIST  9500      // LOCKSTEP: tools/jump_title/gen_fx.py SIGN_DIST = make_sign_card.py (the card is sized at
                                    // it; behind both gunships and the crash, inside the sealed sky volume)
#define TOD_JT_SIGN_MODEL "tod_jt_sign_lit"   // the LIT sign card (tools/jump_title/make_sign_card.py; zoned as an xmodel)
#define TOD_JT_HOST_LINGER 2.5      // s the glows' host keeps riding the sign after a full scene (the blaze fades ~1.8 s after _end)
#define TOD_JT_WATCHDOG   17        // real s after the start: nothing of the scene outlives this (the flight is 12.1)
// THE EYE TRACE (fifth pass; the user: "when you're going down he's kind of wavering up and down"): the local camera's
// position every CLIENT frame for TRACE_UP_SECS from the start (the launch, smooth by the user's account) and for
// TRACE_DOWN_SECS from the end beat (the swing back + the fall: the judder). The lines show whether the rider's eye moves
// in 50 ms plateaus (the mover's trajectory clamping between snapshots) or oscillates. TEMPORARY: zero both before a
// publish (they print ~600 lines per first flight at 165 fps).
#define TOD_JT_TRACE_UP_SECS   0.6
#define TOD_JT_TRACE_DOWN_SECS 3.0
#define TOD_JT_ALIAS_WARP    "tod_jt_warp"        // a ship arriving (3D, panned from the ship)
#define TOD_JT_ALIAS_JET     "tod_jt_jet"         // each gunship's engines from its warp to the crash (3D loop, tod_jt_engine.wav:
                                                  // full level out to 12,000 u, so both ships read over the music)
#define TOD_JT_ALIAS_CHARGE  "tod_jt_charge"      // both engines flaring (2D)
#define TOD_JT_ALIAS_BOOM    "tod_jt_boom"        // THE crash (2D)
#define TOD_JT_ALIAS_RUMBLE  "tod_jt_rumble"      // its rolling tail (2D)
#define TOD_JT_ALIAS_IGNITE  "tod_jt_ignite"      // the sign's power surge (2D), at THE REVEAL
#define TOD_JT_ALIAS_POWER   "zmb_turn_on"        // stock: the power switch's own "it's on" (the lever pulled at the alarm)
#define TOD_JT_ALIAS_LAUGH   "tod_spin_vo_sign_laugh"   // THE DEALER LAUGHS as the sign holds lit (user 2026-09-30; a 2D row in tod_shop.csv, tools/black_market_vo)

// THE FLICKER (the reveal): the card ON / OFF / ON / OFF / ON / OFF for these ms, then steady ON - a neon sign taking
// power. LOCKSTEP: gen_fx.py reads this table (the blaze glows start when the card holds); test_jump_title.js
// bounds its length. An even count of entries: the last is an OFF, then the steady ON.
function flicker_ms()
{
	return array( 70, 60, 50, 100, 120, 50 );
}

REGISTER_SYSTEM( "tod_jump_title", &__init__, undefined )

function __init__()
{
	level.tod_jt = [];
	level.tod_jt_lit = [];      // localClientNum -> the persistent lit sign card (spawned hidden by the first scene)
	level.tod_jt_lit_on = [];   // localClientNum -> true once the sign has been lit on this client (it stays lit)
	level.tod_jt_lit_pending = [];   // localClientNum -> true while a scene thread is spawning its card
	level thread listen( "tod_jump_title_start" );
	level thread listen( "tod_jump_title_ships" );
	level thread listen( "tod_jump_title_impact" );
	level thread listen( "tod_jump_title_ignite" );
	level thread listen( "tod_jump_title_end" );
	log( "INIT rev=" + TOD_JT_REV + " crash=" + TOD_JT_CRASH + " run=" + TOD_JT_RUN + " run_secs=" + TOD_JT_RUN_SECS
		+ " warp=" + TOD_JT_WARP_A + "/" + TOD_JT_WARP_B + " reveal=+" + TOD_JT_REVEAL + " sign=" + TOD_JT_SIGN_YAW + "/" + TOD_JT_SIGN_EL
		+ " dist=" + TOD_JT_SIGN_DIST + " card=" + TOD_JT_SIGN_MODEL + " flicker_ms=" + flicker_total_ms() );
}

// One listener per beat. A start builds a scene; every other beat is handed to that local client's scene.
function listen( note )
{
	while ( true )
	{
		level waittill( note, localClientNum );
		if ( !isdefined( localClientNum ) )
			localClientNum = 0;
		if ( note == "tod_jump_title_start" )
			level thread scene( localClientNum );
		else
			level notify( "tod_jt_beat_" + localClientNum, note );
	}
}

// ---- THE SCENE ------------------------------------------------------------------------------------------------
function scene( localClientNum )
{
	// a new start replaces an old scene on this client (never in play; belt and braces)
	if ( isdefined( level.tod_jt[ localClientNum ] ) )
		cleanup( localClientNum, level.tod_jt[ localClientNum ], "replaced" );
	s = SpawnStruct();
	s.fx = [];
	s.snd = [];
	s.ships = [];
	s.beats = [];
	s.t0 = GetRealTime();
	s.done = false;
	level.tod_jt[ localClientNum ] = s;
	level thread watchdog( localClientNum, s );
	level thread clock_probe( s );

	// THE SIGN: the glows' host rides the sign's bearing; the LIT card loads hidden on the same bearing (the sky's own
	// sign is dull by itself now). A client that has already lit its sign keeps it lit (a second scene: tuning only).
	s.host = sign_host( localClientNum );
	if ( dropped( localClientNum, s ) )
		return;
	lit_card( localClientNum );
	if ( dropped( localClientNum, s ) )
		return;

	// THE STANDOFF: A (magenta) south of the crash point and high, B (green) north and low; bows facing.
	// Loaded HIDDEN now (a model's first frame can take a moment); each appears only with its warp flash.
	d = run_dir();
	a0 = TOD_JT_CRASH - d * ( TOD_JT_BOW + TOD_JT_RUN );
	b0 = TOD_JT_CRASH + d * ( TOD_JT_BOW + TOD_JT_RUN );
	s.ships[ 0 ] = ship_spawn( localClientNum, "tod_sky_gunship", a0, ( TOD_JT_DIVE, 90, 0 ) );
	s.ships[ 1 ] = ship_spawn( localClientNum, "tod_sky_gunship_b", b0, ( 0 - TOD_JT_DIVE, 270, 0 ) );
	if ( dropped( localClientNum, s ) )
		return;
	level thread warp_in( localClientNum, s );
	level thread eye_trace( localClientNum, "up", TOD_JT_TRACE_UP_SECS );
	log( "START client=" + localClientNum + " cam=" + GetCamPosByLocalClientNum( localClientNum ) + " a=" + a0 + " b=" + b0
		+ " ships=" + count_defined( s.ships ) + " host=" + isdefined( s.host ) + " card=" + isdefined( level.tod_jt_lit[ localClientNum ] )
		+ " already_lit=" + IS_TRUE( level.tod_jt_lit_on[ localClientNum ] ) + " load_secs=" + since( s ) );

	while ( !s.done )
	{
		level waittill( "tod_jt_beat_" + localClientNum, note );
		if ( s.done || level.tod_jt[ localClientNum ] !== s )
			return;
		if ( IS_TRUE( s.beats[ note ] ) )
			continue;   // a repeated beat: each is played once per scene
		s.beats[ note ] = true;
		if ( note == "tod_jump_title_ships" )
			charge( localClientNum, s );
		else if ( note == "tod_jump_title_impact" )
			impact( localClientNum, s );
		else if ( note == "tod_jump_title_ignite" )
			ignite( localClientNum, s );
		else if ( note == "tod_jump_title_end" )
			finish( localClientNum, s );
	}
}

// The scene was cut while this thread waited on a model's first frame: whatever it has just made goes too (never
// the lit card: it belongs to the client, not the scene).
function dropped( localClientNum, s )
{
	if ( !s.done )
		return false;
	foreach ( ship in s.ships )
		ship_gone( localClientNum, ship );
	s.ships = [];
	if ( isdefined( s.host ) )
		s.host Delete();
	s.host = undefined;
	return true;
}

// The approach line: A's direction of travel (north, TOD_JT_DIVE deg down); B flies the reverse.
function run_dir()
{
	return ( 0, cos( TOD_JT_DIVE ), 0 - sin( TOD_JT_DIVE ) );
}

// ---- THE SKY SIGN'S HOST AND THE LIT CARD ---------------------------------------------------------------------
function sign_dir()
{
	return AnglesToForward( ( 0 - TOD_JT_SIGN_EL, TOD_JT_SIGN_YAW, 0 ) );
}

// The frame both ride: on the sign's bearing, TOD_JT_SIGN_DIST out, facing back along it (local Y = the sign's
// right, local Z = the sign's up: the frame the glows are laid out in and the card is authored in).
function sign_angles()
{
	return ( TOD_JT_SIGN_EL, TOD_JT_SIGN_YAW + 180, 0 );
}

// A tag_origin for the glows, moved with the camera every frame.
function sign_host( localClientNum )
{
	host = spawn( localClientNum, GetCamPosByLocalClientNum( localClientNum ) + sign_dir() * TOD_JT_SIGN_DIST, "script_model" );
	if ( !isdefined( host ) )
		return undefined;
	host.angles = sign_angles();
	host SetModel( "tag_origin" );
	host util::waittill_dobj( localClientNum );
	if ( !isdefined( host ) )
		return undefined;
	host thread sign_follow( localClientNum );
	return host;
}

// THE LIT SIGN CARD, one per client, spawned HIDDEN the first time a scene asks for it and kept for the match:
// the same painting and card geometry as the sky's dull sign, on the same bearing, so it sits exactly over it.
// -> the card, or undefined when the entity pool refused it (logged; the scene then shows the glows alone).
function lit_card( localClientNum )
{
	card = level.tod_jt_lit[ localClientNum ];
	if ( isdefined( card ) )
		return card;
	if ( IS_TRUE( level.tod_jt_lit_pending[ localClientNum ] ) )
		return undefined;   // another scene thread is spawning it this instant
	level.tod_jt_lit_pending[ localClientNum ] = true;
	card = spawn( localClientNum, GetCamPosByLocalClientNum( localClientNum ) + sign_dir() * TOD_JT_SIGN_DIST, "script_model" );
	if ( isdefined( card ) )
	{
		card.angles = sign_angles();
		card SetModel( TOD_JT_SIGN_MODEL );
		card Hide();   // dull until THE REVEAL lights it
		card util::waittill_dobj( localClientNum );
	}
	level.tod_jt_lit_pending[ localClientNum ] = undefined;
	if ( !isdefined( card ) )
	{
		log( "LIT_FAIL client=" + localClientNum + " the sign card could not be spawned (entity pool): the glows play alone" );
		return undefined;
	}
	card thread sign_follow( localClientNum );
	level.tod_jt_lit[ localClientNum ] = card;
	if ( IS_TRUE( level.tod_jt_lit_on[ localClientNum ] ) )
		card Show();   // this client lit its sign in an earlier scene: it stays lit
	return card;
}

function sign_follow( localClientNum )
{
	self endon( "entityshutdown" );
	dir = sign_dir();
	while ( isdefined( self ) )
	{
		self.origin = GetCamPosByLocalClientNum( localClientNum ) + dir * TOD_JT_SIGN_DIST;
		WAIT_CLIENT_FRAME;
	}
}

// After a full scene the host keeps riding the sign while the blaze fades out, then goes.
function host_linger()
{
	self endon( "entityshutdown" );
	waitrealtime( TOD_JT_HOST_LINGER );
	if ( isdefined( self ) )
		self Delete();
}

// THE SIGN LIGHTS: with the flicker (the reveal) or at once (a scene cut after the ignite). Idempotent: once lit,
// lit. The card stays shown for the rest of the match on this client.
function sign_on( localClientNum, why, flicker )
{
	card = lit_card( localClientNum );
	if ( !IS_TRUE( level.tod_jt_lit_on[ localClientNum ] ) && isdefined( card ) && flicker )
	{
		p = flicker_ms();
		for ( i = 0; i + 1 < p.size; i += 2 )
		{
			if ( !isdefined( card ) )
				break;
			card Show();
			waitrealtime( p[ i ] / 1000.0 );
			if ( !isdefined( card ) )
				break;
			card Hide();
			waitrealtime( p[ i + 1 ] / 1000.0 );
		}
	}
	level.tod_jt_lit_on[ localClientNum ] = true;
	if ( isdefined( card ) )
		card Show();
	log( "LIT client=" + localClientNum + " why=" + why + " flicker=" + flicker + " card=" + isdefined( card ) );
}

function flicker_total_ms()
{
	p = flicker_ms();
	n = 0;
	foreach ( ms in p )
		n += ms;
	return n;
}

// ---- THE SHIPS ----------------------------------------------------------------------------------------------------
function ship_spawn( localClientNum, model, origin, angles )
{
	ship = spawn( localClientNum, origin, "script_model" );
	if ( !isdefined( ship ) )
		return undefined;
	ship.angles = angles;
	ship SetModel( model );
	ship Hide();   // never seen before its warp flash (the camera may be looking anywhere at the launch)
	ship.tod_jt_home = origin;
	ship util::waittill_dobj( localClientNum );
	if ( !isdefined( ship ) )
		return undefined;
	return ship;
}

// THE ARRIVAL: A as the turn brings it into frame, then B; the charge brings in any ship still hidden (a
// client that fell behind), so the ram never happens in an empty sky. Real seconds from the start beat.
function warp_in( localClientNum, s )
{
	wait_scene_time( s, TOD_JT_WARP_A );
	if ( s.done ) return;
	arrive( localClientNum, s, 0 );
	wait_scene_time( s, TOD_JT_WARP_B );
	if ( s.done ) return;
	arrive( localClientNum, s, 1 );
}

// Real seconds until the scene is `t` old (at once if it already is: the ships' first frames can eat into it).
function wait_scene_time( s, t )
{
	left = t - since( s );
	if ( left > 0 )
		waitrealtime( left );
}

// One ship out of the warp: the portal flash where it hangs, the bamf panned from it, its engines lit.
function arrive( localClientNum, s, i )
{
	ship = s.ships[ i ];
	if ( !isdefined( ship ) || IS_TRUE( ship.tod_jt_here ) )
		return;
	ship.tod_jt_here = true;
	s.fx[ "warp" + i ] = PlayFX( localClientNum, "tod/jump/fx_jt_warp", ship.origin, AnglesToForward( ship.angles ), ( 0, 0, 1 ) );
	s.snd[ "warp" + i ] = PlaySound( localClientNum, TOD_JT_ALIAS_WARP, ship.origin );
	ship Show();
	ship.tod_jt_eng = PlayFXOnTag( localClientNum, "tod/sky/fx_sky_eng_gunship", ship, "tag_origin" );
	ship PlayLoopSound( TOD_JT_ALIAS_JET, 0.6 );
	ship thread hover( s );
	log( "WARP client=" + localClientNum + " ship=" + i + " t=" + since( s ) + " at=" + ship.origin
		+ " dist=" + int( Distance( GetCamPosByLocalClientNum( localClientNum ), ship.origin ) ) );
}

// The standoff's idle: a slow bob until the charge (a hovering warship reads as alive, and as waiting). Set each
// frame from the real clock (a MoveTo rides the frame-counted script clock).
function hover( s )
{
	self endon( "entityshutdown" );
	self endon( "tod_jt_charge" );
	t0 = GetRealTime();
	while ( isdefined( self ) && !s.done )
	{
		a = ( GetRealTime() - t0 ) / 1000.0 * 360.0 / TOD_JT_BOB_SECS;   // degrees (GSC's sin)
		self.origin = self.tod_jt_home + ( 0, 0, TOD_JT_BOB * sin( a ) );
		WAIT_CLIENT_FRAME;
	}
}

// THE CHARGE: both engines flare (a white-hot burn at every nozzle) and they accelerate into each other.
function charge( localClientNum, s )
{
	d = run_dir();
	ends = array( TOD_JT_CRASH - d * TOD_JT_BOW, TOD_JT_CRASH + d * TOD_JT_BOW );
	for ( i = 0; i < s.ships.size; i++ )
	{
		arrive( localClientNum, s, i );   // a no-op unless this client fell behind the warp
		ship = s.ships[ i ];
		if ( !isdefined( ship ) )
			continue;
		ship notify( "tod_jt_charge" );
		ship thread ram( s, ends[ i ] );
		ship.tod_jt_burn = PlayFXOnTag( localClientNum, "tod/jump/fx_jt_burn", ship, "tag_origin" );   // stops with the ship
	}
	s.snd[ "charge" ] = PlaySound( localClientNum, TOD_JT_ALIAS_CHARGE, GetCamPosByLocalClientNum( localClientNum ) );
	log( "CHARGE client=" + localClientNum + " t=" + since( s ) + " ships=" + count_defined( s.ships ) );
}

// The ram: from where the ship hangs to the contact in TOD_JT_RUN_SECS of REAL time, all acceleration, so the
// bows meet exactly on the impact beat at any frame rate.
function ram( s, to )
{
	self endon( "entityshutdown" );
	from = self.origin;
	t0 = GetRealTime();
	ms = TOD_JT_RUN_SECS * 1000.0;
	while ( isdefined( self ) && !s.done )
	{
		f = ( GetRealTime() - t0 ) / ms;
		if ( f >= 1 )
		{
			self.origin = to;
			return;
		}
		self.origin = from + ( to - from ) * ram_curve( f );
		WAIT_CLIENT_FRAME;
	}
}

// The share of the run done at f (0..1): speeding up for TOD_JT_RUN_ACCEL of it, then flat out (the same curve as
// tools/jump_title/scene_geometry.js trapezoid( t, T, T * 0.85, 0 ), which the gate and the storyboard fly).
function ram_curve( f )
{
	a = TOD_JT_RUN_ACCEL;
	v = 1.0 / ( 1.0 - a / 2.0 );
	if ( f < a )
		return 0.5 * v * f * f / a;
	return 0.5 * v * a + v * ( f - a );
}

// THE CRASH: the fireball and the boom at the contact; the hulls go under the full white.
function impact( localClientNum, s )
{
	cam = GetCamPosByLocalClientNum( localClientNum );
	s.fx[ "boom" ] = PlayFX( localClientNum, "tod/jump/fx_jt_boom", TOD_JT_CRASH, ( 1, 0, 0 ), ( 0, 0, 1 ) );
	s.snd[ "boom" ] = PlaySound( localClientNum, TOD_JT_ALIAS_BOOM, cam );
	s.snd[ "rumble" ] = PlaySound( localClientNum, TOD_JT_ALIAS_RUMBLE, cam );
	level thread under_white( localClientNum, s );
	level thread aftershocks( localClientNum, s );
	log( "IMPACT client=" + localClientNum + " t=" + since( s ) + " cam=" + cam + " dist=" + int( Distance( cam, TOD_JT_CRASH ) ) );
}

// The screen is FULL white from 0.06 to 0.31 s after the impact (TodJumpCine): the hulls go inside that window,
// so they are never seen to vanish (the fireball, the reactor blasts and the wreckage replace them).
function under_white( localClientNum, s )
{
	waitrealtime( TOD_JT_UNDER_WHITE );
	if ( s.done ) return;
	foreach ( ship in s.ships )
		ship_gone( localClientNum, ship );
	s.ships = [];
}

// The chain reaction: the two reactors go up a beat apart, and the wreckage falls burning toward the city.
function aftershocks( localClientNum, s )
{
	waitrealtime( 0.28 );
	if ( s.done ) return;
	s.fx[ "blast0" ] = PlayFX( localClientNum, "tod/jump/fx_jt_blast", TOD_JT_WRECK_A, ( 1, 0, 0 ), ( 0, 0, 1 ) );
	waitrealtime( 0.22 );
	if ( s.done ) return;
	s.fx[ "blast1" ] = PlayFX( localClientNum, "tod/jump/fx_jt_blast", TOD_JT_WRECK_B, ( 1, 0, 0 ), ( 0, 0, 1 ) );
	s.fx[ "wreck0" ] = PlayFX( localClientNum, "tod/jump/fx_jt_wreck", TOD_JT_WRECK_A, ( 1, 0, 0 ), ( 0, 0, 1 ) );
	s.fx[ "wreck1" ] = PlayFX( localClientNum, "tod/jump/fx_jt_wreck", TOD_JT_WRECK_B, ( 1, 0, 0 ), ( 0, 0, 1 ) );
}

// THE IGNITION beat: behind the full white nothing visible changes (the sign stays dull under the fire); it arms
// THE REVEAL on this client's real clock. From here a cut scene still lights the sign (cleanup).
function ignite( localClientNum, s )
{
	level thread reveal( localClientNum, s );
	log( "IGNITE client=" + localClientNum + " t=" + since( s ) + " host=" + isdefined( s.host ) + " card=" + isdefined( level.tod_jt_lit[ localClientNum ] ) );
}

// THE REVEAL: the fire in front has thinned: the power surge is heard NOW (at the ignite it would be buried under
// the boom), the sign FLICKERS ON (the card over the dull bake), and once it holds the blaze glows ramp up over it,
// the crest's ring and its eyes flare a beat apart, the sparks rain off the letters (gen_fx.py's own curves).
function reveal( localClientNum, s )
{
	t_ignite = since( s );
	waitrealtime( TOD_JT_REVEAL );
	if ( s.done ) return;   // cut before the reveal: cleanup() has lit the sign at once
	cam = GetCamPosByLocalClientNum( localClientNum );
	s.snd[ "ignite" ] = PlaySound( localClientNum, TOD_JT_ALIAS_IGNITE, cam );
	s.snd[ "power" ] = PlaySound( localClientNum, TOD_JT_ALIAS_POWER, cam );
	log( "REVEAL client=" + localClientNum + " t=" + since( s ) + " after_ignite=" + ( since( s ) - t_ignite ) );
	sign_on( localClientNum, "reveal", true );   // the flicker, in real time; the sign holds lit after it
	if ( s.done ) return;
	// THE DEALER LAUGHS at the lit sign (user 2026-09-30: "one of the black market dealer laughs when the sign shows"):
	// 2D on this client, in s.snd so a cut scene stops it with the rest
	s.snd[ "laugh" ] = PlaySound( localClientNum, TOD_JT_ALIAS_LAUGH, cam );
	log( "LAUGH client=" + localClientNum + " t=" + since( s ) + " alias=" + TOD_JT_ALIAS_LAUGH );
	if ( isdefined( s.host ) )
		s.fx[ "blaze" ] = PlayFXOnTag( localClientNum, "tod/jump/fx_jt_blaze", s.host, "tag_origin" );
	else   // no host (its spawn failed): the same glows from where the sign is right now
		s.fx[ "blaze" ] = PlayFX( localClientNum, "tod/jump/fx_jt_blaze", cam + sign_dir() * TOD_JT_SIGN_DIST,
		                          AnglesToForward( sign_angles() ), AnglesToUp( sign_angles() ) );
	log( "BLAZE client=" + localClientNum + " t=" + since( s ) + " blaze=" + isdefined( s.fx[ "blaze" ] ) + " host=" + isdefined( s.host ) );
}

// THE END of a full scene: StopFX lets live particles finish their own fade as the sign leaves the frame (the host
// keeps the blaze on the sign until it is out); the sounds ring out. A cut-short scene drops everything at once.
function finish( localClientNum, s )
{
	full = IS_TRUE( s.beats[ "tod_jump_title_ignite" ] );
	if ( full )
		level thread eye_trace( localClientNum, "down", TOD_JT_TRACE_DOWN_SECS );   // the swing back and the fall
	log( "END client=" + localClientNum + " t=" + since( s ) + " full=" + full + " ships_left=" + count_defined( s.ships ) );
	cleanup( localClientNum, s, ( ( full ) ? "end" : "cut" ) );
}

function cleanup( localClientNum, s, why )
{
	if ( s.done )
		return;
	s.done = true;
	// the crash happened (the ignite beat came) but the scene is over: the sign is lit, never dull after the crash
	if ( IS_TRUE( s.beats[ "tod_jump_title_ignite" ] ) && !IS_TRUE( level.tod_jt_lit_on[ localClientNum ] ) )
		level thread sign_on( localClientNum, why, false );
	foreach ( ship in s.ships )
		ship_gone( localClientNum, ship );
	s.ships = [];
	keys = GetArrayKeys( s.fx );
	foreach ( k in keys )
	{
		if ( !isdefined( s.fx[ k ] ) )
			continue;
		if ( why == "end" )
			StopFX( localClientNum, s.fx[ k ] );   // live particles finish their own fade
		else
			KillFX( localClientNum, s.fx[ k ] );   // cut short: nothing of the scene lingers under the menu that cut it
	}
	s.fx = [];
	if ( why != "end" )
	{
		keys = GetArrayKeys( s.snd );
		foreach ( k in keys )
		{
			if ( isdefined( s.snd[ k ] ) )
				StopSound( s.snd[ k ] );
		}
		log( "CLEANUP client=" + localClientNum + " why=" + why + " t=" + since( s ) + " lit=" + IS_TRUE( level.tod_jt_lit_on[ localClientNum ] ) );
	}
	s.snd = [];
	if ( isdefined( s.host ) )
	{
		if ( why == "end" )
			s.host thread host_linger();
		else
			s.host Delete();
	}
	s.host = undefined;
	if ( level.tod_jt[ localClientNum ] === s )
		level.tod_jt[ localClientNum ] = undefined;
}

// THE EYE TRACE: one line per client frame, real time, the camera's position (see the defines). A level thread: it
// outlives the scene on purpose (the fall is after the end beat).
function eye_trace( localClientNum, tag, secs )
{
	if ( secs <= 0 )
		return;
	t0 = GetRealTime();
	n = 0;
	while ( GetRealTime() - t0 < secs * 1000 )
	{
		c = GetCamPosByLocalClientNum( localClientNum );
		log( "TRACE " + tag + " ms=" + ( GetRealTime() - t0 ) + " x=" + c[ 0 ] + " y=" + c[ 1 ] + " z=" + c[ 2 ] );
		n++;
		WAIT_CLIENT_FRAME;
	}
	log( "TRACE " + tag + " done frames=" + n + " secs=" + secs );
}

function watchdog( localClientNum, s )
{
	waitrealtime( TOD_JT_WATCHDOG );
	if ( !s.done )
	{
		log( "WATCHDOG client=" + localClientNum + " t=" + since( s ) + " (the _end never came)" );
		cleanup( localClientNum, s, "watchdog" );
	}
}

// THE CLOCKS, once per scene: a one-second script `wait` against the real clock. The first play measured 2.7x (a
// frame-counted wait at ~165 fps); this file never times anything with `wait`, and the record says why it must not.
function clock_probe( s )
{
	t0 = GetRealTime();
	wait 1;   // the script clock ON PURPOSE (the only one in this file; test_jump_title allows it here alone)
	log( "CLOCK script_wait_1s_took_real=" + ( ( GetRealTime() - t0 ) / 1000.0 ) + " scene_t=" + since( s ) );
}

function ship_gone( localClientNum, ship )
{
	if ( !isdefined( ship ) )
		return;
	ship notify( "tod_jt_charge" );
	if ( isdefined( ship.tod_jt_eng ) )
		StopFX( localClientNum, ship.tod_jt_eng );
	if ( isdefined( ship.tod_jt_burn ) )
		StopFX( localClientNum, ship.tod_jt_burn );
	ship StopAllLoopSounds( 0.1 );
	ship Delete();
}

function count_defined( a )
{
	n = 0;
	foreach ( e in a )
	{
		if ( isdefined( e ) )
			n++;
	}
	return n;
}

function since( s )
{
	return ( GetRealTime() - s.t0 ) / 1000.0;
}

function log( msg )
{
	if ( !TOD_JT_LOG ) return;
	line = "[TOD_JT] ms=" + GetRealTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}
