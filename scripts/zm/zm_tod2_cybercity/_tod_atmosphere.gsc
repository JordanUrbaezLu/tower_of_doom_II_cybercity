// =============================================================================
// _tod_atmosphere.gsc — the tower's air: a cold neon city smog.
//
// ⚠️ THE 8-ARG OVERLOAD HAS NO OPACITY ARGUMENT. The header here used to read
// "SetVolFog( ..., r,g,b, maxOpacity ) — the stock 8-arg builtin", and that was
// WRONG for the life of this map. The 8th slot is <transition time>. Corrected
// 2026-08-30 (v14.37) against three independent sources:
//   1. <modtools>/docs_modtools/bo3_scriptapifunctions.htm — the 8-arg form
//      ends `<red>,<green>,<blue>,<TRANSITION TIME>`; <fog max opacity> exists
//      only in the 18-arg form, as arg 17.
//   2. Stock's ONLY call site, load_shared.gsc:807, passes 0.4 there — a
//      0.4-SECOND blend for a fog-volume trigger. (This is the very cite the
//      old header used to claim the opposite; it was misread.)
//   3. <modtools>/source_data/fog.gdt "default" ships "fogopacity" "0", and
//      our worldspawn declares `"fsi" "default"` — so max opacity booted at
//      ZERO and no 8-arg call could ever raise it.
// USER CONFIRMED LIVE: "Yes this map has never rendered fog." Every fog value
// in this file was tuned against a preview tool and had never been seen.
//
// ⚠️⚠️ AND THE ARG COUNT WAS NOT THE ROOT CAUSE ANYWAY (v14.41, the real one).
// `fsi` — the FOG SETTINGS asset baked from worldspawn — was `default`, whose
// fog.gdt entry carries "fogopacity" "0". The fog system was CLAMPED OFF at
// asset level, so no SetVolFog of any arity could ever have drawn. Fixed in
// tools/gen_tower_map.js: fsi -> `zm_factory_volumetric` (stock zm_factory's
// own entry, fogopacity 1). THAT is why the map now has air.
//
// SO WE ARE BACK ON THE 8-ARG FORM, DELIBERATELY (set_fog):
//   1 startDist 2 halfwayDist 3 halfwayHeight 4 baseHeight
//   5 red 6 green 7 blue 8 TRANSITION TIME
// v14.37 briefly moved to the 18-arg overload to reach <fogMaxOpacity>. It was
// reverted before shipping because that overload is used NOWHERE in the entire
// mod tools install (the only SetVolFog anywhere is load_shared.gsc:807, and it
// is 8-arg) — an unverified signature is not what you ship on the one feature
// the user said must not come back broken. With the fsi fixed it buys nothing.
// DENSITY IS CONTROLLED BY halfwayDist / halfwayHeight, real args of the proven
// call: shorter halfwayDist = thicker; larger halfwayHeight = holds with
// altitude. Opacity is the fsi's job now, map-wide.
// Pure script -> ships with a linker-only build, can never regress the bake.
//
// DESIGN: the haze is densest at street level (baseHeight 0) and halves every
// TOD_FOG_HALFWAY_HEIGHT units of altitude — so the base arena sits in thick
// purple-blue smog, the low laps fade the city below into glow, and by the
// mid-tower you have CLIMBED OUT of it into clear night air under the night
// skyline dome. Height-as-progress, told through the air. AS OF v14.37 THIS
// DESCRIBES SOMETHING THAT ACTUALLY RENDERS — read every value below as
// unproven-in-game until the first live look.
// Color must stay LIGHTER than scene-black or it reads as nothing (map 1
// lesson: near-black fog = invisible).
// =============================================================================

#using scripts\shared\flag_shared;
#using scripts\shared\util_shared;   // waittill_any_timeout: the band's wait also ends on the first jump's title (docs/196)
#using scripts\zm\zm_tod2_cybercity\_tod_breather_data;   // GENERATED — lounge z list + pad anchor (v16.7 lounge FX / arrival chime)
#using scripts\zm\zm_tod2_cybercity\_tod_arena_data;     // GENERATED — in_arena(): the Battle Arena room is not a floor (2026-09-28)
#using scripts\zm\zm_tod2_cybercity\_tod_house_data;   // GENERATED - in_house / in_parlour: THE DEALER'S HOUSE is not a floor either (docs/207)
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;     // GENERATED — transit_hall_fx(): the departure hall's ambience (docs/196)

#insert scripts\shared\shared.gsh;

#define TOD_FOG_START_DIST      300    // units from camera where haze begins
#define TOD_FOG_HALFWAY_DIST    2600   // distance to half opacity (open-air scale)
#define TOD_FOG_HALFWAY_HEIGHT  1200   // altitude falloff — thick low, clear by mid-tower
#define TOD_FOG_BASE_HEIGHT     0      // densest at street level
#define TOD_FOG_R               0.16   // cold purple-blue neon smog
#define TOD_FOG_G               0.14
#define TOD_FOG_B               0.30
// ⚠️ NOT AN OPACITY — this is passed as arg 8 of the 8-arg form, which is the
// TRANSITION TIME. Kept under its historical name only because it is threaded
// through set_fog's callers; read it as "the fog blend takes 0.38s". THE MAP'S
// ACTUAL OPACITY IS THE fsi ASSET (zm_factory_volumetric, fogopacity 1) — to
// make the tower's fog thinner or thicker, move TOD_FOG_HALFWAY_DIST (bigger =
// thinner) or switch the fsi to zm_factory_afog (fogopacity 0.5) in the
// generator. Do NOT expect changing this number to change density.
#define TOD_FOG_OPACITY         0.38
// Blend time for every ordinary fog write. Short enough to feel immediate,
// long enough that the two apply_fog asserts do not visibly pop.
#define TOD_FOG_TRANSITION      0.5

// ---- THE VEIL (user 2026-09-25) --------------------------------------------
// "the skybox is going to be very, very detailed ... I do kind of want to add
// this fog to the map, but until the power is on. And once the power is on,
// all that fog will clear up and that skybox will become visible ... the
// typical way to do fog is to place it on the tower and then shift it once
// power's on. Instead of making it disappear, I think it breaks sometimes."
//
// So: from the blackscreen the tower sits in a dense, even haze that hides the
// sky (the sky is fogged at worldfogskysize 65,000 by the fsi, so at a 520
// halfway distance it is 100% veil colour). THE LEVER (the power) starts a
// LERP, not a kill: every 0.1 s the halfway distance is pushed out on a cubic
// ease from TOD_VEIL_HALFDIST to TOD_VEIL_FAR_HALFDIST over TOD_VEIL_CLEAR_SECS
// through the same change-gated set_fog every fog write uses (proven in game), and
// only once the lerp is DONE does the loop fall back to the exact fog_off()
// state the tower has run in since v14.42 — the state every build before this
// one shipped, so the cleared map cannot differ from the map the user knows.
// The veil rides apply_fog's authority loop (last writer wins on a global
// SetVolFog), keyed on the Fall: up while
// level.tod_fall_phase holds and the flood has not started; clearing from
// level.tod_fall_power_ms (the POWER SWITCH at the overlook, 2026-09-25 — it was
// the alarm's flood until the two switches split);
// off for good after. A map without the Fall never sees it (old behaviour).
// Colour must stay lighter than scene-black (map 1's rule) or it reads as
// nothing: a cold ash, a shade lighter than the tower's own smog. One knob
// per symptom: too thick/thin = HALFDIST (inverse); clears too fast/slow =
// CLEAR_SECS; wrong colour = R/G/B; sky still hazy at the end = FAR_HALFDIST.
// Each lerp tick is one SetVolFog (and one stock "Old syntax used" console
// line) — ~10/s for CLEAR_SECS, then silence.
#define TOD_VEIL                 0          // OFF (user 2026-09-25: "I tried to add some fog I actually want to remove that") — the tower is fog_off() again; 1 = the veil below
#define TOD_VEIL_HALFDIST        520        // the veil's density (inverse: smaller = thicker)
#define TOD_VEIL_HALFHEIGHT      1000000    // no altitude falloff (a halving height far past the world): even from the plaza to the crown
#define TOD_VEIL_R               0.22       // cold ash, lighter than scene-black
#define TOD_VEIL_G               0.20
#define TOD_VEIL_B               0.26
#define TOD_VEIL_FAR_HALFDIST    60000      // the lerp's end: under the sky's 65,000 fog distance the sky is clear again
#define TOD_VEIL_CLEAR_SECS      12         // pull -> clear (the siren's wind-up is 10 s; the reveal lands as the flood arrives)
#define TOD_VEIL_LOG             1          // [TOD_VEIL] prints with dev OFF for the first playtests — zero before publish

// ---- MUSIC BANDS (v9.46, user 2026-08-23) --------------------------------
// LAP_RISE mirrored from tools/gen_tower_map.js (and from _tod_gauge's own
// copy of it). Duplicated rather than imported: _tod_gauge::floor_of returns a
// gauge CELL (2 floors per cell, 1..26), not a floor, so there is nothing there
// to reuse — and a #using into the gauge would couple the music channel to the
// HUD for one integer.
#define TOD_MUSIC_LAP_RISE      384
#define TOD_MUSIC_POLL_SECS     2      // how often the band watcher re-reads the party's high point
// docs/160 — THE DESCENT: the party starts at the crown, so the latch that
// drives the bands is a LOW-water mark (the lowest floor any live player has
// reached) instead of the high-water. The band table is unchanged, so the
// climb's order plays in reverse — eclipse from the crown, withyou from 41,
// cornfield from 33, city from 25, the base track (Reykjavik) from 17, relay
// (Meteor Herd) from 8 down to the ground (2026-10-01; register_music_bands
// owns the numbers). With the climb latch the crown
// would pin "Cyber Eclipse" for all fifty floors. LOCKSTEP with DESCENT in
// gen_tower_map.js; 0 restores the climb latch.
#define TOD_MUSIC_DESCENT       1
#define TOD_MUSIC_TOP_FLOOR     999    // the low-water's starting value: above every band row
// THE INTRO (user 2026-09-24: "a thirty-second WAV file that will play at the
// beginning of the map when all the players spawn in, and then it'll go into
// silence once it's done"). One 2D one-shot at the blackscreen, then NO band
// while the party is in the crown — the hall is the lever's silence, the
// siren is its sound. The bands start when the crown seals behind the party
// (level.tod_fall_phase drops); a map without the Fall starts them at once.
// tod_fall_intro = sound/aliases/tod_ui.csv (STREAMED 2D LOOPING so it can be
// STOPPED — by its own clock or by the lever, never overlapping the siren;
// sound_assets/tod/music/tod_fall_intro.wav = the user's "Deep Mystery.wav",
// 30.2 s, matched to -12.9 LUFS / -1 dBTP). 0 = the old behaviour.
#define TOD_MUSIC_INTRO         1
#define TOD_MUSIC_INTRO_ALIAS   "tod_fall_intro"
#define TOD_MUSIC_INTRO_SECS    30.2
#define TOD_MUSIC_EE_GAP        3.0    // v18.96b (user: "3 seconds of silence ... Give some tension"): the old track stops, the room goes quiet, then the song
#define TOD_MUSIC_EE_SECS       279.3  // v18.96: the teddy-bear song's measured length (tod_music_ee.wav = "Falling To Pieces", ffprobe 279.33 s) — the channel is handed back after it
// PK03 THE END-OF-RUN MUSIC (2026-10-04): the two cues a run ends on, GENERATED by
// tools/sfx/end_of_run_music/make_sounds.py (sound/aliases/tod_ui.csv: STREAMED 2D NONLOOPING
// on BUS_MUSIC at the bands' loudness). Its --check gate holds the two alias names and
// TOD_HOUSE_VICTORY_SECS to its manifest (LOCKSTEP: a re-picked take moves the hold). See
// gameover_play / house_victory_start below.
#define TOD_MUSIC_GAMEOVER          1     // 0 = the old silence (and stock's own game_over state comes back)
#define TOD_MUSIC_GAMEOVER_ALIAS    "tod_music_gameover"
#define TOD_HOUSE_VICTORY_ALIAS     "tod_house_victory"
#define TOD_HOUSE_VICTORY_SECS      18.2  // the cue's music + its last reverb: the channel stays parked this long, then the band
#define TOD_HOUSE_VICTORY_FADE      1.0   // "115" fades under the cue's quiet first second (StopLoopSound's fade) instead of a hard cut

// v16.7 LOUNGE AMBIENCE — every one of these ALSO has an `fx,` line in
// zone_source (the pairing rule: a precache without the zone line resolves
// to nothing and PlayFX silently no-ops — the rampage spark's lesson).
#precache( "fx", "tod/haven/fx_tod_haven_motes" );   // PK43: the map's own motes (tools/haven/make_fx.py); env/light/fx_light_god_rays_dust_motes is a placeholder stub here
#precache( "fx", "dirt/fx_dust_linger_int_sector" );
#precache( "fx", "fog/fx_fog_ground_wind_lt_sm" );
#precache( "fx", "steam/fx_steam_leak_sm_soft_slow" );
#define TOD_LOUNGE_CHIME_ALIAS   "tod_lounge_arrive"   // sound/aliases/tod_ui.csv, 2D non-looping
#define TOD_LOUNGE_POLL_SECS     0.5
// ONE SWITCH for the script half of the v16.7 lounge pass (user: "I may want
// to revert"): 0 = no lounge FX, no arrival chime. The zone fx lines and the
// alias stay (harmless unused). The geometry half is BR_POLISH in the
// generator. This is a -GscOnly change.
#define TOD_LOUNGE_AMBIENCE      1

#namespace tod_atmosphere;

function init()
{
	// PK03: stock's music system asks this before it sets a music state; "game_over" is ours (gameover_play)
	level.sndPlayStateOverride = &snd_play_state_override;
	level thread apply_fog();
	level thread ambient_music();
	if ( TOD_LOUNGE_AMBIENCE )
	{
		level thread lounge_fx();
		level thread lounge_arrival_watch();
	}
}

// ---------------------------------------------------------------------------
// v16.7 — THE LOUNGES BREATHE (user 2026-09-01: "continue enhance however we
// can"). The script half of the breather polish pass; the brushwork half is
// gen_tower_map.js §v16.7 and the record is docs/42.
//
// 1. AMBIENT FX per lounge — persistent LOOPING effects placed with server
//    PlayFX at fixed points after the blackscreen. THE RENDER LANE, PROVEN:
//    map 1's _acc_atmosphere::fx_at placed ~40 of these exactly this way and
//    they draw (its own note: "loops via fx_at DO, proven" — it is one-shot
//    server PlayFX that does not, which is why every burst in this map rides
//    a tag_origin host). Each asset has BOTH the #precache above AND an `fx,`
//    line in zone_source. All four are stock, map-1-proven on this same tools
//    install, and none carries a particlecloud reference (the pcloud crash
//    class that took out the green fungus pod on map 1).
//      motes  tod/haven/fx_tod_haven_motes            a shaft of drifting
//             (PK43, 2026-10-05: GENERATED, tools/haven/make_fx.py - the
//             stock env/light/fx_light_god_rays_dust_motes it replaces is a
//             gfx_debug_missing_fx PLACEHOLDER in the tools root, so zoning it
//             shipped the stub and the shaft never drew)
//             motes falling from the open top into the room, lit by the
//             lounge's theme lights
//      haze   dirt/fx_dust_linger_int_sector          slow interior dust —
//             the "subtle life" layer map 1 gave every zone
//      fog    fog/fx_fog_ground_wind_lt_sm            ground fog curling over
//             the teleporter pad floating in the void
//      vent   steam/fx_steam_leak_sm_soft_slow        one soft vent at the
//             foot of the spur gate's east post
//    Placed under the blackscreen so they are alive at fade-in (map 1: "start
//    everything at once"); a late joiner sees an ongoing loop like any map FX.
//    Coordinates are the EVEN/mirrored frame every lounge sits in, z and the
//    pad point from the generated breather data — the furniture's own
//    no-drift contract.
//
// 2. ARRIVAL CHIME — the first time each player walks INTO each lounge they
//    hear a short 2D chime (tod_lounge_arrive, a rising synth arpeggio; the
//    non-caption lane, per the user's no-floaty-text rule). Nothing else marks
//    reaching a breather except the floor-10 music change, and the full-map
//    review's A8 asked for exactly this beat. At most four per player per run.
//    The footprint box is _tod_breather_data::lounge_index_at's (the haven hall:
//    docs/202 v2). Since docs/202 v3 the spawn calm (_tod_endless_rounds::
//    tod_player_in_breather) asks the haven's FIELD instead, so the chime and the
//    calm no longer share a box on purpose: the chime greets the hall, the calm
//    rewards standing in the taken sanctuary.
// ---------------------------------------------------------------------------

function lounge_fx()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	if ( !isdefined( level._effect ) )
		level._effect = [];
	level._effect[ "tod_lounge_motes" ] = "tod/haven/fx_tod_haven_motes";   // PK43 (the key also feeds tod_crown_data::transit_hall_fx)
	level._effect[ "tod_lounge_haze" ]  = "dirt/fx_dust_linger_int_sector";
	level._effect[ "tod_lounge_fog" ]   = "fog/fx_fog_ground_wind_lt_sm";
	level._effect[ "tod_lounge_vent" ]  = "steam/fx_steam_leak_sm_soft_slow";
	zs = tod_breather_data::breather_zs();
	for ( i = 0; i < zs.size; i++ )
	{
		z = zs[ i ];
		// THE HAVENS (docs/202): the rest stop is a safe-zone dome now, and the
		// field's own looping effect (_tod_haven) is the life inside it. The
		// stock loops keep the approach: motes falling through the open
		// threshold, fog curling over the teleporter pad, a soft vent beside the
		// threshold's south-east gate post. Anchors GENERATED (haven_layout.js).
		lounge_fx_at( "tod_lounge_motes", tod_breather_data::haven_motes_org( z ) );
		pad = tod_breather_data::tp_pad_org( z );
		lounge_fx_at( "tod_lounge_fog",   ( pad[ 0 ], pad[ 1 ], z + 4 ) );
		lounge_fx_at( "tod_lounge_vent",  tod_breather_data::haven_vent_org( z ) );
	}
	// docs/196 THE DEPARTURE HALL (the top teleporter bay): motes falling through
	// the oculus, a slow haze in the crossing, wind-fog curling at the open window —
	// the lounges' own three stock loops, at anchors GENERATED from
	// tower_transit_layout.js FX (tod_crown_data::transit_hall_fx).
	hall = tod_crown_data::transit_hall_fx();
	for ( i = 0; i < hall.size; i++ )
		lounge_fx_at( hall[ i ].fx, hall[ i ].org );
}

function lounge_fx_at( key, origin )
{
	if ( isdefined( level._effect[ key ] ) )
		PlayFX( level._effect[ key ], origin );
}

function lounge_arrival_watch()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	zs = tod_breather_data::breather_zs();
	for ( ;; )
	{
		wait TOD_LOUNGE_POLL_SECS;
		players = GetPlayers();
		for ( i = 0; i < players.size; i++ )
		{
			p = players[ i ];
			if ( !isdefined( p ) || !IsAlive( p ) )
				continue;
			// ALIVE + PLAYING ONLY — a spectator's origin rides the camera
			// (the gauge's own rule), and a chime for a dead player is noise.
			if ( isdefined( p.sessionstate ) && p.sessionstate != "playing" )
				continue;
			j = lounge_index_at( p.origin, zs );
			if ( j < 0 )
				continue;
			if ( !isdefined( p.tod_lounge_seen ) )
				p.tod_lounge_seen = [];
			if ( IS_TRUE( p.tod_lounge_seen[ j ] ) )
				continue;
			p.tod_lounge_seen[ j ] = true;
			p PlayLocalSound( TOD_LOUNGE_CHIME_ALIAS );
		}
	}
}

// -> the lounge index (0..3) whose hall box holds this point, else -1 (the
// generated _tod_breather_data::lounge_index_at: the haven hall, its porch and
// its loggia). It takes in the doorway on purpose, so the chime lands as you
// step through the arch, not three strides later.
function lounge_index_at( o, zs )
{
	return tod_breather_data::lounge_index_at( o );
}

// ---------------------------------------------------------------------------
// MUSIC — this module is the ONE owner of the music channel.
//
// Base state (user 2026-08-19): ONE low background track on repeat. v9.46
// (user 2026-08-23) makes that the FIRST of several — the track changes as the
// party climbs past the breather floors, see register_music_bands(). PANZER
// OVERRIDE (user 2026-08-19, reaffirmed 2026-08-23 "boss music will always
// override this"): the boss track (tod_boss_music, "115") owns the channel for
// the Battle Arena's fights (arena_music_start/end). The Panzer refcount that
// first owned it and the finale's latch retired whole 2026-10-05.
//
// THE STOPPABLE PRIMITIVE (map 1's 5-fix music saga): a streamed track is
// only stoppable as PlayLoopSound of a LOOPING alias on a script_origin;
// stop = StopLoopSound(0) + StopSound(alias) + StopSounds() + a Delete
// DEFERRED one frame. NONLOOPING streamed one-shots are engine-unstoppable.
// ---------------------------------------------------------------------------

function ambient_music()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	level.tod_music_floor = 0;          // party high-water mark, latched (see below)
	if ( TOD_MUSIC_DESCENT )
		level.tod_music_floor = TOD_MUSIC_TOP_FLOOR;   // docs/160: a LOW-water mark now — starts above every row
	register_music_bands();
	level thread music_end_watch();
	if ( TOD_MUSIC_INTRO )
	{
		intro_play();   // blocks for the intro (or until the lever cuts it)
		// silence until the crown seals (the Fall's phase ends) — OR until a living
		// player steps onto THE JUMP-PAD BALCONY (user 2026-09-29: "the first song starts
		// up once you enter the crown balcony that the jump pad lives on. No mid air on
		// the jump pad. That way music is started already and cinematic view is enhanced
		// with the music"; the box is GENERATED, tod_crown_data::jumppad_balcony_mins/maxs).
		// The first jump's title reveal (docs/196: _tod_jumppad cine_reveal notifies
		// "tod_jump_title") stays as the fallback cue. Bounded only by the match.
		cue = undefined;
		while ( IS_TRUE( level.tod_fall_phase ) )
		{
			p = balcony_player();
			if ( isdefined( p ) )
			{
				cue = "player " + p GetEntityNumber() + " stepped onto the jump-pad balcony";
				break;
			}
			if ( IS_TRUE( level.tod_jump_title ) )
			{
				cue = "the first jump's title reveal";
				break;
			}
			level util::waittill_any_timeout( 0.25, "tod_jump_title" );
		}
		if ( isdefined( cue ) )
			music_log( "BAND cued: " + cue + " (the crown is not sealed yet)" );
		if ( isdefined( level.tod_music_cur ) )
		{
			level thread music_band_watch();
			return;   // something else (a boss track) already owns the channel; the watch takes over after it
		}
	}
	channel_play( band_alias() );
	level thread music_band_watch();
}

// -> a living player standing on THE JUMP-PAD BALCONY (the GENERATED launch-deck box), or
// undefined. The first band's cue (ambient_music): the song is already up when the jump's
// opening scene plays.
function balcony_player()
{
	if ( !tod_crown_data::jumppad_enabled() )
		return undefined;
	mn = tod_crown_data::jumppad_balcony_mins();
	mx = tod_crown_data::jumppad_balcony_maxs();
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || !IsAlive( p ) || ( isdefined( p.sessionstate ) && p.sessionstate != "playing" ) )
			continue;
		o = p.origin;
		if ( o[ 0 ] >= mn[ 0 ] && o[ 0 ] <= mx[ 0 ] && o[ 1 ] >= mn[ 1 ] && o[ 1 ] <= mx[ 1 ] && o[ 2 ] >= mn[ 2 ] && o[ 2 ] <= mx[ 2 ] )
			return p;
	}
	return undefined;
}

// The intro rides the music CHANNEL as a LOOPING streamed alias (the only
// engine-stoppable shape: PlayLoopSound + channel_stop's three calls), and is
// stopped by script at its own length — OR the instant the lever is pulled
// (user 2026-09-24: "if they trigger the switch before the 30-second sound is
// up, then it will end the 30-second sound and start the siren. They should
// never overlap"). The pull flag rises before the 0.3 s handle flip; the
// siren starts after it, so the cut always lands first.
function intro_play()
{
	channel_play( TOD_MUSIC_INTRO_ALIAS );
	line = "[TOD_MUSIC] ms=" + GetTime() + " INTRO " + TOD_MUSIC_INTRO_ALIAS + " up for " + TOD_MUSIC_INTRO_SECS + " s or until the lever, then silence until the crown seals";
	/#
	PrintLn( line );
	#/
	cut = false;
	for ( t = 0; t < TOD_MUSIC_INTRO_SECS * 10; t++ )
	{
		wait 0.1;
		if ( IS_TRUE( level.tod_fall_lever_pulled ) || IS_TRUE( level.tod_fall_flood ) )
		{
			cut = true;
			break;
		}
	}
	if ( isdefined( level.tod_music_cur ) && level.tod_music_cur == TOD_MUSIC_INTRO_ALIAS )
		channel_stop();
	line = "[TOD_MUSIC] ms=" + GetTime() + " INTRO " + ( cut ? "CUT by the lever" : "ended" );
	/#
	PrintLn( line );
	#/
}

// ---------------------------------------------------------------------------
// MUSIC BANDS (v9.46, user 2026-08-23: "at each 10 level there is a breather
// station. On each of these levels we will change the background track").
//
// THE TABLE IS THE WHOLE FEATURE. Each row is (first floor, alias); the base
// track covers everything below the lowest row. band_alias() picks the HIGHEST
// row whose floor the party has reached, so a band with no track yet simply
// has no row and the previous one keeps playing — never silence, never an
// alias that does not exist. Adding the missing breather tracks later is one
// line here + one alias row in sound/aliases/tod_ui.csv + one wav.
//
// ROWS ARE ORDERED LOW -> HIGH and band_alias() scans BACKWARDS. Keep them
// sorted; an out-of-order row would shadow the ones above it.
function register_music_bands()
{
	level.tod_music_bands = [];
	// EVENLY DISTRIBUTED ACROSS 10-50 (user 2026-08-25: "Those 3 songs from 10-50.
	// Distribute evenly through the 40 rounds"). Was 20/30/40, briefly 10/30/40.
	//
	// 41 floors (10..50) over 3 tracks = 13.67 each, so the split cannot be exact:
	//   city    10-22   13 floors
	//   relay   23-36   14 floors
	//   eclipse 37-50   14 floors
	// The SHORT band is deliberately first, so the opening change still lands on
	// the floor-10 breather; putting it last would have made the final stretch of
	// the climb the one that felt clipped.
	//
	// NOTE THIS DECOUPLES THE MUSIC FROM THE BREATHERS. Only floor 10 is still a
	// rest stop; 23 and 37 land mid-climb, so the track now changes while the
	// party is moving. That is the cost of an even split and it is intentional —
	// the breather-aligned alternative is 10/20/30, which leaves eclipse carrying
	// 21 floors.
	// 2026-09-29 (user: "I also want this song as part of the tower. ItsArius &
	// Lynnic - Cornfield Chase", placed in the MIDDLE): FIVE EVEN BANDS OF 10.
	// Going DOWN: 50-41 Champs, 40-31 Meteor Herd, 30-21 Cornfield Chase,
	// 20-11 Una Mattina, 10-1 Reykjavik. (Was 50-37 / 36-23 / 22-10 / 9-1.)
	// 2026-09-30 (user: "I also like the song With You by Lynnic but I dont want
	// vocals"): a SIXTH band, the vocal-free "With You" (Lynnic, ItsArius & Dinia;
	// vocals separated with demucs htdemucs_ft, no official instrumental exists).
	// SIX BANDS over 50 floors = 8.33 each, so the split is 9/8/8/8/9/8 going
	// DOWN: 50-42 Champs, 41-34 Meteor Herd, 33-26 With You, 25-18 Cornfield
	// Chase, 17-9 Una Mattina, 8-1 Reykjavik. With You sits between the two
	// faster tracks and the two Lynnic ones; the user never said WHERE, so the
	// slot is the one assumption of that pass — move its row (and the floors
	// in the README table) if it belongs elsewhere.
	// 2026-10-01 (user: "We should [move] meteor herd to the bottom floor"): Meteor Herd
	// takes the LAST band and everything above it shifts down one slot. Its row starts
	// at floor 0 ON PURPOSE: music_floor_of() returns 0 below z 0 (the Undercity), so a
	// floor-0 row means the bottom band also owns the ground and band_alias()'s literal
	// fallback (tod_ambient_music, Reykjavik) can no longer surface under the tower.
	// Going DOWN: 50-42 Champs, 41-34 With You, 33-26 Cornfield Chase, 25-18 Una
	// Mattina, 17-9 Reykjavik, 8-ground Meteor Herd.
	add_music_band( 0, "tod_music_relay" );      // floors 8-1 + the ground: "Meteor Herd" instrumental (Sonic Adventure 2)
	add_music_band( 9, "tod_ambient_music" );    // floors 17-9:  "Reykjavik" (Joachim Pastor)
	add_music_band( 18, "tod_music_city" );      // floors 25-18: "Una Mattina" (Lynnic)
	add_music_band( 26, "tod_music_cornfield" ); // floors 33-26: "Cornfield Chase" (ItsArius & Lynnic) — 2026-09-29
	add_music_band( 34, "tod_music_withyou" );   // floors 41-34: "With You" instrumental + its melody on a synth (Lynnic, ItsArius & Dinia) — 2026-09-30
	add_music_band( 42, "tod_music_eclipse" );   // floors 50-42, the FIRST band after the crown seals: "La Clé des Champs" (N'to)
	// (the boss slot tod_boss_music = "115" extended, played in the Battle Arena; band_alias()'s literal fallback is unreachable while a floor-0 row exists)
	// Adding another band is one line here + an alias row + a wav, nothing else.
	// Keep the rows in ASCENDING floor order: band_alias() walks the array
	// backwards and returns the first row at or below the current floor.
}

function add_music_band( first_floor, alias )
{
	b = SpawnStruct();
	b.floor = first_floor;
	b.alias = alias;
	level.tod_music_bands[ level.tod_music_bands.size ] = b;
}

// -> the alias the CURRENT band wants. Base track when below every row.
function band_alias()
{
	if ( !isdefined( level.tod_music_bands ) )
		return "tod_ambient_music";
	f = ( ( isdefined( level.tod_music_floor ) ) ? level.tod_music_floor : 0 );
	for ( i = level.tod_music_bands.size - 1; i >= 0; i-- )
	{
		if ( f >= level.tod_music_bands[ i ].floor )
			return level.tod_music_bands[ i ].alias;
	}
	return "tod_ambient_music";
}

// Real floor 1..LAPS for a world z (the gauge's cell math deliberately not
// reused — see the TOD_MUSIC_LAP_RISE note).
function music_floor_of( z )
{
	if ( z < 0 )
		return 0;
	return 1 + int( z / TOD_MUSIC_LAP_RISE );
}

// The band watcher. Reads the HIGHEST floor any live player stands on and
// LATCHES it — walking back down the stairs never rewinds the music. That is
// deliberate: the bands are progression, not a location, and an un-latched
// version would re-cue the stream every time someone crossed a threshold at a
// breather (a stream cannot seek, so every re-cue restarts the track from 0).
//
// BOSS ALWAYS WINS (user: "boss music will always override this"). While the
// Battle Arena or the teddy-bear song holds the channel, the band still UPDATES
// but never swaps the stream — arena_music_end / ee_song_run then resume into
// whatever band the party is in by then.
function music_band_watch()
{
	level endon( "end_game" );
	for ( ;; )
	{
		wait TOD_MUSIC_POLL_SECS;

		high = level.tod_music_floor;
		players = GetPlayers();
		foreach ( p in players )
		{
			if ( !isdefined( p ) || !isplayer( p ) )
				continue;
			// 2026-09-28: the Battle Arena room stands at z 0 = "floor 1"; a
			// player in it would drop the descent's low-water to 1 and swap in
			// the floors 9-1 track (the user's 23:52 run: ARENA_END resumed
			// tod_ambient_music from floor 40) - and unlock every song for the
			// after-arena random pick.
			if ( tod_arena_data::in_arena( p.origin ) || tod_house_data::in_house( p.origin ) || tod_house_data::in_parlour( p.origin ) )
				continue;
			// No laststand check on purpose: the mark is LATCHED, and a player
			// who went down on floor 31 did reach floor 31. Filtering them would
			// only matter if the mark could fall, which it cannot.
			// docs/160: a SPECTATOR's origin rides a teammate's camera, which
			// under the descent's low-water latch is harmless (it can only
			// report a floor a live player is on).
			f = music_floor_of( p.origin[ 2 ] );
			if ( TOD_MUSIC_DESCENT )
			{
				if ( f < high )
					high = f;   // the low-water (the variable keeps its name: it is "the latch")
			}
			else if ( f > high )
				high = f;
		}
		if ( high == level.tod_music_floor )
			continue;

		was = band_alias();
		level.tod_music_floor = high;
		now = band_alias();
		if ( now == was )
			continue;                   // climbed, but inside the same band

		// The arena or the song owns the channel: keep the latch, leave the stream.
		if ( IS_TRUE( level.tod_music_ee ) || IS_TRUE( level.tod_arena_music ) )
			continue;   // (v18.96: the teddy-bear song too — ee_song_run resumes into band_alias() when it ends; 2026-09-28: the Battle Arena too — arena_music_end resumes the band)
		channel_play( now );
	}
}

// GAME OVER STOP (v9.26, session 2a's ship-state audit 2026-08-23):
// channel_stop was only ever reached THROUGH channel_play, so the looping
// emitter outlived end_game and kept playing under stock's game-over sting —
// and under the v9.24 Restart Map / End Game menu. Stop the channel the moment
// the game ends, win or wipe. Nothing can restart it afterwards: every caller
// of channel_play runs under a level endon("end_game"). Own thread on purpose — ambient_music's
// endon would kill this watcher with it.
// PK03 (2026-10-04): and the run now ENDS on its own cue instead of silence (gameover_play).
function music_end_watch()
{
	level waittill( "end_game" );
	channel_stop();
	gameover_play();
}

// ---------------------------------------------------------------------------
// PK03 — THE END-OF-RUN MUSIC (2026-10-04). Two generated cues
// (tools/sfx/end_of_run_music/make_sounds.py; sound/aliases/tod_ui.csv):
//   THE LOSS     tod_music_gameover: a ~13 s dark-synth defeat cadence the moment the run
//                ends (music_end_watch, right after the channel stops). Until now the GAME
//                OVER - FLOOR N screen and the restart menu played whatever stock's own
//                "game_over" music state found: a sting this map does not own (TOD1's
//                tester heard stock's round_end state the same way), or nothing.
//                snd_play_state_override takes that ONE state from stock's music system
//                (every other state is untouched), so exactly one game-over cue plays
//                whichever way the stock lane behaves.
//   THE VICTORY  tod_house_victory: beating THE DEALER (_tod_arena::arena_win, the house's
//                level, docs/207). Until now his death played the same 2.85 s fanfare as
//                levels 1-9 while "115" kept looping. The cue opens near-silent on purpose:
//                it starts ~1.75 s into his 6.25 s death line and sits under it, then rises
//                and lands on its major chord.
// BOTH ARE ONE-SHOTS ON THEIR OWN EMITTER, NOT THE CHANNEL. The channel's shape (a LOOPING
// alias stopped by script) loops audibly the moment the server pauses: the script clock
// stops and the audio does not (UIN_MOD rows are not pauseable). In solo the game-over
// restart menu IS a pause (it opens 3 s in), and a pause menu during the victory's card
// deal is the same. A NONLOOPING cue plays once whatever the clock does. While the victory
// plays the CHANNEL is held instead: every request (the arena's ride home, the band
// watcher) is parked, and the newest one plays when the cue has rung out
// (TOD_HOUSE_VICTORY_SECS). The teddy-bear song still outranks it (house_victory_start
// refuses under the song; ee_song_start cuts it).
// Logs `[TOD_MUSIC] GAMEOVER ...` / `VICTORY ...` (music_log: dev / diag).
// ---------------------------------------------------------------------------

// level.sndPlayStateOverride (stock _zm_audio::playState asks it before music::setmusicstate):
// true = this state is ours, do not set it. Only game_over; everything else goes to stock.
function snd_play_state_override( state )
{
	if ( TOD_MUSIC_GAMEOVER && isdefined( state ) && state == "game_over" )
	{
		music_log( "GAMEOVER stock_state=taken (the map's own cue plays)" );
		return true;
	}
	return false;
}

function gameover_play()
{
	if ( !TOD_MUSIC_GAMEOVER )
		return;
	// the teddy-bear song's and the victory's latches die with their end_game-killed
	// threads: neither may outlive the run or park the last cue
	level.tod_music_ee = false;
	level.tod_music_ee_pending = undefined;
	house_victory_cut( "the game over" );
	level.tod_music_gameover_ent = sting_play( TOD_MUSIC_GAMEOVER_ALIAS );
	music_log( "GAMEOVER play alias=" + TOD_MUSIC_GAMEOVER_ALIAS + " players=" + GetPlayers().size );
}

// PUBLIC — _tod_arena::arena_win at the Dealer's level. -> false when the teddy-bear song
// holds the channel (nothing overtakes it: the caller plays the level fanfare instead).
function house_victory_start()
{
	if ( IS_TRUE( level.tod_music_ee ) )
	{
		music_log( "VICTORY refused: the teddy-bear song holds the channel (the level fanfare plays instead)" );
		return false;
	}
	if ( IS_TRUE( level.tod_music_victory ) )
		return true;
	level.tod_music_victory = true;
	level.tod_music_victory_pending = undefined;
	was = ( isdefined( level.tod_music_cur ) ? level.tod_music_cur : "none" );
	channel_fade( TOD_HOUSE_VICTORY_FADE );
	level.tod_music_victory_ent = sting_play( TOD_HOUSE_VICTORY_ALIAS );
	level thread house_victory_run();
	music_log( "VICTORY play alias=" + TOD_HOUSE_VICTORY_ALIAS + " faded=" + was + " hold=" + TOD_HOUSE_VICTORY_SECS + "s" );
	return true;
}

function house_victory_run()
{
	level endon( "end_game" );
	level endon( "tod_music_victory_cut" );
	wait TOD_HOUSE_VICTORY_SECS;
	house_victory_release();
}

// the cue has rung out: the channel is free and the newest parked request plays (the
// arena's ride home parks its random band here). Nobody asked = silence until someone
// does, which is the state the channel would be in anyway.
function house_victory_release()
{
	if ( !IS_TRUE( level.tod_music_victory ) )
		return;
	level.tod_music_victory = false;
	if ( isdefined( level.tod_music_victory_ent ) )
		level.tod_music_victory_ent Delete();   // its one-shot has ended: only the emitter is freed
	level.tod_music_victory_ent = undefined;
	next = level.tod_music_victory_pending;
	level.tod_music_victory_pending = undefined;
	music_log( "VICTORY rang_out resume=" + ( isdefined( next ) ? next : "none" ) );
	if ( isdefined( next ) )
		channel_play( next );
}

// the cue cut short (the game over, or the teddy-bear song, which outranks everything).
// -> the request it had parked (undefined if none). The stop is best effort: a streamed
// one-shot may outlive every stop (the channel header's note), which is why the cue never
// relies on one.
function house_victory_cut( why )
{
	if ( !IS_TRUE( level.tod_music_victory ) )
		return undefined;
	level.tod_music_victory = false;
	level notify( "tod_music_victory_cut" );
	sting_stop( level.tod_music_victory_ent, TOD_HOUSE_VICTORY_ALIAS );
	level.tod_music_victory_ent = undefined;
	next = level.tod_music_victory_pending;
	level.tod_music_victory_pending = undefined;
	music_log( "VICTORY cut by " + why + " parked=" + ( isdefined( next ) ? next : "none" ) );
	return next;
}

// a one-shot music cue on its own emitter in the channel's open-air spot (a 2D alias on an
// entity reaches every client, like the channel's loop)
function sting_play( alias )
{
	e = Spawn( "script_origin", ( 0, -490, 100 ) );
	e PlaySound( alias );
	return e;
}

function sting_stop( e, alias )
{
	if ( !isdefined( e ) )
		return;
	e StopSound( alias );
	e StopSounds();
	level thread music_ent_delete( e );
}

// hand the channel's stream a FADE instead of a cut (StopLoopSound's fade time, stock's own
// use), then the full stop on that emitter once the fade is done. The channel is free at
// once: whatever plays next spawns its own emitter.
function channel_fade( secs )
{
	if ( !isdefined( level.tod_music_ent ) )
		return;
	e = level.tod_music_ent;
	alias = level.tod_music_cur;
	level.tod_music_ent = undefined;
	level.tod_music_cur = undefined;
	e StopLoopSound( secs );
	level thread channel_fade_finish( e, alias, secs );
}

// no endon( "end_game" ) on purpose: a fade in flight at the game over still finishes its stop
function channel_fade_finish( e, alias, secs )
{
	wait secs + 0.05;
	if ( !isdefined( e ) )
		return;
	if ( isdefined( alias ) )
		e StopSound( alias );
	e StopSounds();
	e Delete();
}

// PUBLIC (2026-09-28, user: the boss music "115" plays in the Battle Arena
// fights). _tod_arena calls these at the jump in and the jump back. A latch,
// not a refcount: one arena trip at a time. A wipe inside is game over, and
// music_end_watch stops the channel on end_game.
function arena_music_start()
{
	if ( IS_TRUE( level.tod_arena_music ) )
		return;
	level.tod_arena_music = true;
	channel_play( "tod_boss_music" );   // parked by channel_play while the teddy-bear song holds
	music_log( "ARENA_START alias=tod_boss_music cur=" + ( isdefined( level.tod_music_cur ) ? level.tod_music_cur : "none" ) );
}

// -> every floor track the party has already UNLOCKED: the band it is in now
// and every band it has passed through. Under THE DESCENT (low-water latch)
// that is the band holding level.tod_music_floor and every band ABOVE it;
// under the climb latch, that band and every band BELOW it. The base track
// ("tod_ambient_music", floors below the first row) counts as a band.
function unlocked_band_aliases()
{
	out = [];
	if ( !isdefined( level.tod_music_bands ) || level.tod_music_bands.size == 0 )
	{
		out[ 0 ] = "tod_ambient_music";
		return out;
	}
	f = ( ( isdefined( level.tod_music_floor ) ) ? level.tod_music_floor : 0 );
	bands = level.tod_music_bands;
	if ( TOD_MUSIC_DESCENT )
	{
		if ( f < bands[ 0 ].floor )
			out[ out.size ] = "tod_ambient_music";
		for ( i = 0; i < bands.size; i++ )
		{
			// band i covers floors [ bands[i].floor, bands[i+1].floor - 1 ] (the last one has no top)
			if ( i == bands.size - 1 || bands[ i + 1 ].floor > f )
				out[ out.size ] = bands[ i ].alias;
		}
	}
	else
	{
		out[ out.size ] = "tod_ambient_music";
		for ( i = 0; i < bands.size; i++ )
		{
			if ( f >= bands[ i ].floor )
				out[ out.size ] = bands[ i ].alias;
		}
	}
	if ( out.size == 0 )
		out[ 0 ] = band_alias();
	return out;
}

// 2026-09-28 (user): "After a battle arena wave the tower music will play a
// random song that has already been unlocked" — the return from an arena trip
// picks at random among unlocked_band_aliases() instead of the current band.
// The pick plays until the party descends into a NEW band (the watcher only
// re-cues on a band change) or the next arena trip takes the channel.
function arena_music_end()
{
	if ( !IS_TRUE( level.tod_arena_music ) )
		return;
	level.tod_arena_music = false;
	pool = unlocked_band_aliases();
	next = pool[ RandomInt( pool.size ) ];
	pool_str = "";
	foreach ( a in pool )
		pool_str += ( ( pool_str == "" ) ? "" : "," ) + a;
	music_log( "ARENA_RANDOM floor=" + level.tod_music_floor + " pool=" + pool_str + " pick=" + next );
	if ( !isdefined( level.tod_music_cur ) || level.tod_music_cur != next )
		channel_play( next );   // while the teddy-bear song holds this only overwrites the parked request
	music_log( "ARENA_END resume=" + next );
}

function music_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_MUSIC] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// PUBLIC (v18.96) — THE TEDDY BEAR SONG (_tod_secret: shoot all three bears).
// USER RULE: "make sure it cant be overridden by boss music. No music can
// overtake this EE song." So it OUTRANKS EVERYTHING — the Battle Arena's boss
// track and the Dealer's victory cue. The gate is in channel_play itself:
// while the song holds, any other request is PARKED (the newest wins) and
// replayed the moment the song ends; nothing else in this file needs to know.
// Once per match (the secret is once per match). -> true if the song started.
// lead_secs (v18.96c, optional): extra silence BEFORE the gap — the third
// bear's rise-and-flight plays under it, then TOD_MUSIC_EE_GAP of true quiet.
function ee_song_start( lead_secs )
{
	if ( IS_TRUE( level.tod_music_ee ) || IS_TRUE( level.tod_music_ee_played ) )
		return false;
	level.tod_music_ee_lead = 0;
	if ( isdefined( lead_secs ) && lead_secs > 0 )
		level.tod_music_ee_lead = lead_secs;
	level.tod_music_ee = true;
	level.tod_music_ee_played = true;
	level.tod_music_ee_pending = house_victory_cut( "the teddy-bear song" );   // PK03: it outranks the Dealer's victory too; the band the victory had parked waits behind the song
	// THE GAP: silence first (the latch above already holds the channel, so
	// nothing can slip in during it), then the song.
	channel_stop();
	level thread ee_song_run();
	return true;
}

function ee_song_run()
{
	level endon( "end_game" );
	if ( isdefined( level.tod_music_ee_lead ) && level.tod_music_ee_lead > 0 )
		wait level.tod_music_ee_lead;
	wait TOD_MUSIC_EE_GAP;
	channel_play( "tod_music_ee" );
	wait TOD_MUSIC_EE_SECS;
	level.tod_music_ee = false;
	// Whoever asked last while the song held gets the channel back; nobody
	// asked = the state the channel would be in anyway.
	next = level.tod_music_ee_pending;
	level.tod_music_ee_pending = undefined;
	if ( !isdefined( next ) )
	{
		if ( IS_TRUE( level.tod_arena_music ) )
			next = "tod_boss_music";
		else
			next = band_alias();
	}
	channel_play( next );
}

// Hard-swap the channel to `alias` (stop-then-play — never two streams).
// v18.96: WHILE THE TEDDY BEAR SONG HOLDS, NOTHING ELSE PLAYS — the request
// is parked and replayed when the song ends (ee_song_run). See ee_song_start.
// Emitter sits in OPEN AIR at the spawn area — (0,0,0) is INSIDE the solid
// core brush (the aliases are 2d so it should not matter, but a possibly
// occluded emitter was one suspect in the silent-music live test).
function channel_play( alias )
{
	if ( IS_TRUE( level.tod_music_ee ) && isdefined( alias ) && alias != "tod_music_ee" )
	{
		level.tod_music_ee_pending = alias;   // v18.96: parked until the teddy-bear song ends (user: no music can overtake it)
		return;
	}
	if ( IS_TRUE( level.tod_music_victory ) && isdefined( alias ) )
	{
		level.tod_music_victory_pending = alias;   // PK03: parked until the Dealer's victory cue rings out (house_victory_release)
		return;
	}
	channel_stop();
	e = Spawn( "script_origin", ( 0, -490, 100 ) );
	level.tod_music_ent = e;
	level.tod_music_cur = alias;
	e PlayLoopSound( alias );
}

function channel_stop()
{
	if ( !isdefined( level.tod_music_ent ) )
		return;
	e = level.tod_music_ent;
	alias = level.tod_music_cur;
	level.tod_music_ent = undefined;
	level.tod_music_cur = undefined;
	e StopLoopSound( 0 );
	if ( isdefined( alias ) )
		e StopSound( alias );
	e StopSounds();
	level thread music_ent_delete( e );
}

function music_ent_delete( e )
{
	wait 0.05;
	if ( isdefined( e ) )
		e Delete();
}

// v14.42 — THE TOWER GETS NO FOG. STANDING RULE (user 2026-08-31: "I dont want
// any changes on the regular play through tower"; the veil was switched off
// again on 2026-09-25 — see TOD_VEIL).
//
// This is why the tower is EXPLICITLY DISABLED rather than simply left alone:
// v14.41 fixed `fsi` to zm_factory_volumetric so the fog system finally works,
// and that asset is a WORLDSPAWN key — it is map-wide. With fog capable
// map-wide, doing nothing here would have handed the tower a visual change it
// must not get. So the tower actively pushes fog beyond the world, and only
// THE VEIL (tower_fog, TOD_VEIL) can ever bring it back.
//
// The push is map 1's proven kill (there is no fog-off builtin): start the fog
// a hundred million units away. Precedent: _acc_atmosphere.gsc:419-422, and
// stock does the same with setExpFog in _art.gsc.
//
// The authored smog constants (TOD_FOG_R/G/B, HALFWAY_*) are KEPT, not deleted:
// they are the map's designed cyber-city haze and the only thing standing
// between them and the screen is one call. If the tower is ever wanted foggy,
// restore the two set_fog lines this function used to make — they are in git
// history at v14.41 — and change nothing else.
// =============================================================================
// THE SINGLE FOG AUTHORITY — ported from map 1's proven implementation
// (_acc_atmosphere.gsc:262-300), because this map's two-shot version did not
// work and map 1's has worked for months.
//
// WHY A LOOP AND NOT TWO CALLS. This function used to call SetVolFog at the
// blackscreen and again 5s later, then exit — and the user's live test found NO
// FOG AT ALL. Map 1 hit the same wall and its own comments name the cause: a
// one-shot SetVolFog does not stick ("a frame-0 SetVolFog was the original 'no
// haze' bug"), so it runs a permanent 0.1s loop it calls "the SINGLE fog
// authority ... so nothing fights it". Stock art paths, fog volumes and the
// client-side visionset monitor all touch fog during and after the fade; the
// only reliable answer is to keep asserting.
//
// TWO THEORIES THIS REPLACES, BOTH MINE AND BOTH WRONG — recorded so nobody
// re-runs them:
//   1. "The 8-arg 8th slot is transition time, not opacity." The API doc does
//      say that, but MAP 1 PASSES OPACITY THERE AND ITS FOG RENDERS. Whatever
//      the doc means, the working reference wins.
//   2. "fsi `default` ships fogopacity 0, so fog is clamped off at asset
//      level." Map 1 uses `fsi "default"`. So does stock zm_giant. Reverted.
// Both were plausible, both were derived from documentation and asset files
// rather than from the working map sitting on the same disk. THE REFERENCE
// IMPLEMENTATION OUTRANKS THE DOCUMENTATION — check it first.
//
// Per the standing instruction the tower's asserted state is fog OFF, so
// regular play is visually identical to every build before this. THE VEIL
// (tower_fog, TOD_VEIL) is the only state that can turn fog on.
function apply_fog()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );

	// Change-gated (map 1's own refinement at _acc_atmosphere.gsc:454): only
	// call SetVolFog when the wanted state actually differs, because
	// re-asserting identical params every tick buried a real fatal under tens
	// of thousands of console lines on that map.
	// NO CHANGE-GATE HERE — but NOT for the reason an earlier version of this
	// comment claimed. It asserted "map 1 re-asserts every tick and that IS the
	// mechanism". THAT IS FALSE, and an audit against the working map caught it:
	// map 1 funnels every write through acc_set_vol_fog()
	// (_acc_atmosphere.gsc:454-470), which builds a key from all 8 args and
	// RETURNS EARLY on a match — so map 1 calls SetVolFog exactly once per
	// parameter CHANGE, and its fog renders fine. Its 0.1s loop exists to notice
	// changes (dvar retunes, the power-on settle), not to re-issue identical
	// values. So a gate is not what broke us.
	//
	// We run ungated anyway, deliberately: it is strictly more robust (it also
	// recovers from any external stomp, which a gate cannot), and at these
	// values it costs one builtin call per 0.1s. The v14.42 gate is still worth
	// naming as a bug — it gated on a value set_fog itself had just written, so
	// it could only ever fire once, which is a broken gate rather than a wrong
	// design. 0.1s matches map 1's cadence.
	for ( ;; )
	{
		// TOWER = THE VEIL until the lever, then its lerp, then NO FOG —
		// re-asserted, so nothing can leak fog into regular play either.
		tower_fog();

		wait 0.1;
	}
}

// THE VEIL's state machine, one call per tick of apply_fog (see the defines).
// f = 0 while the Fall's calm holds, 0..1 over TOD_VEIL_CLEAR_SECS from the
// flood, 1 = the tower's fog_off() state.
function tower_fog()
{
	if ( !TOD_VEIL )
	{
		fog_off();
		return;
	}
	f = 1.0;
	if ( isdefined( level.tod_fall_power_ms ) )
	{
		f = ( GetTime() - level.tod_fall_power_ms ) / ( TOD_VEIL_CLEAR_SECS * 1000.0 );
		if ( f < 0 ) f = 0;
		if ( f > 1 ) f = 1;
	}
	else if ( IS_TRUE( level.tod_fall_phase ) )
	{
		f = 0;   // the calm: the veil is up
	}
	if ( f >= 1 )
	{
		veil_log( "CLEAR" );
		fog_off();
		return;
	}
	if ( f <= 0 )
	{
		veil_log( "UP halfdist=" + TOD_VEIL_HALFDIST );
		set_fog( 0, TOD_VEIL_HALFDIST, TOD_VEIL_HALFHEIGHT, TOD_FOG_BASE_HEIGHT,
			TOD_VEIL_R, TOD_VEIL_G, TOD_VEIL_B, TOD_FOG_TRANSITION );
		return;
	}
	// the lerp: cubic ease on the halfway distance (linear would spend most of
	// the reveal in the first second), colour held, each step a 0.5 s blend
	e = f * f * f;
	halfd = Int( TOD_VEIL_HALFDIST + ( TOD_VEIL_FAR_HALFDIST - TOD_VEIL_HALFDIST ) * e );
	veil_log( "CLEARING f=" + f + " halfdist=" + halfd );
	set_fog( 0, halfd, TOD_VEIL_HALFHEIGHT, TOD_FOG_BASE_HEIGHT,
		TOD_VEIL_R, TOD_VEIL_G, TOD_VEIL_B, TOD_FOG_TRANSITION );
}

// One line per STATE (UP / CLEARING / CLEAR), never per tick: the loop calls
// this ten times a second.
function veil_log( msg )
{
	if ( !TOD_VEIL_LOG && !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	state = msg;
	if ( msg.size > 8 )
		state = GetSubStr( msg, 0, 8 );
	if ( isdefined( level.tod_veil_logged ) && level.tod_veil_logged == state )
		return;
	level.tod_veil_logged = state;
	line = "[TOD_VEIL] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// Fog pushed past the world = fog off (map 1's proven kill at
// _acc_atmosphere.gsc:419-422 — there is no fog-off builtin, so you start the
// fog beyond the world). The tower's default state (tower_fog).
// 2026-10-04 (docs/208) MAP 1's TWO BLACK-SCREEN FIXES, ported (its v19.40 + v19.63, after
// Workshop reports: "everything goes black ... other than shadows ... when someone else is
// hosting it works fine" / "as soon as the weapon classes pop up it goes black"). This tower
// writes fog_off() from initial_blackscreen_passed for the whole match (TOD_VEIL 0), and the
// old arguments divided by zero TWICE in the volumetric fog maths on GPUs that do not clamp:
//   (1) the third argument is the HALFWAY HEIGHT and it was 0 (the numbers came from stock
//       setExpFog, whose zeros are r, g, b): a zero height falloff;
//   (2) 100,000,000 and 100,000,001 are the SAME float32 (its spacing at 1e8 is 8), so the
//       distance term (d - start) / (halfway - start) divided by zero as well.
// The halfway point is now 200,000,000 and the height the veil's own 1,000,000: the density
// ramp starts 100,000,000 units past anything in the world, so nothing is ever fogged and
// the maths stays finite. [TOD_FOG] SET (set_fog, tod_dev) prints each change.
#define TOD_FOG_OFF_START      100000000
#define TOD_FOG_OFF_HALFDIST   200000000
#define TOD_FOG_OFF_HALFHEIGHT 1000000
function fog_off()
{
	set_fog( TOD_FOG_OFF_START, TOD_FOG_OFF_HALFDIST, TOD_FOG_OFF_HALFHEIGHT, 0, 0, 0, 0, 0 );
}

// ONE WRITER, ONE RECORD. Every fog write in this file should go through here
// so level.tod_fog_* stays the truth about what is currently on screen.
// v14.37 — THE TOWER'S FOG NOW ACTUALLY RENDERS (user confirmed live: "Yes
// this map has never rendered fog"). Every call in this file used the 8-arg
// overload, whose 8th slot is TRANSITION TIME, not opacity — so max opacity
// stayed at the fog.gdt "default" value of 0 and the whole cyber-city smog
// design has been invisible since the map was authored. Routed through the
// 18-arg form, which is the only one carrying <fogMaxOpacity>.
// ARG ORDER IS LOAD-BEARING — the 8-arg order is listed in the file header.
// v14.41 — BACK TO THE 8-ARG FORM, ON PURPOSE. v14.37 moved to the 18-arg
// overload to reach <fogMaxOpacity>, having correctly worked out that the
// 8-arg 8th slot is TRANSITION TIME. That diagnosis stands — but the 18-arg
// form is used NOWHERE in the entire mod tools install (checked
// share/raw/scripts: the only SetVolFog anywhere is load_shared.gsc:807, and
// it is 8-arg), so shipping it would have been an unverified signature on the
// one feature the user explicitly said must not come back broken.
// It is also unnecessary now: the real reason fog never drew was `fsi
// "default"` carrying fogopacity 0 (see gen_tower_map.js). With the fsi fixed,
// the PROVEN call is enough — and `op` becomes the TRANSITION TIME it always
// literally was, passed honestly instead of by accident.
// DENSITY IS NOW CONTROLLED BY halfwayDist / halfwayHeight, which are real
// arguments of the proven call: shorter halfwayDist = thicker.
function set_fog( startd, halfd, halfh, baseh, r, g, b, transition )
{
	// v17.43 — CHANGE-GATED, map 1's way (_acc_atmosphere.gsc:454-470: one
	// key from all 8 args, return early on a match). The ungated 0.1 s
	// re-assert in apply_fog() was one engine call AND one console error
	// ("setVolFog: Old syntax used") every 100 ms for the whole match — 1,957
	// lines in a five-minute session on 2026-09-04, on a tower that has no
	// fog at all. The v14.42 gate failed because it compared against a value
	// this function had just written; this key is written ONLY after the
	// builtin call, so the first call of every new state always goes through.
	key = startd + "|" + halfd + "|" + halfh + "|" + baseh + "|" + r + "|" + g + "|" + b + "|" + transition;
	if ( isdefined( level.tod_fog_key ) && level.tod_fog_key == key )
		return;
	SetVolFog( startd, halfd, halfh, baseh, r, g, b, transition );
	level.tod_fog_key = key;
	// docs/208 (map 1's v19.40 log): change-gated above, so a handful of lines per match.
	if ( IS_TRUE( level.tod_dev ) )
	{
		line = "[TOD_FOG] ms=" + GetTime() + " SET start=" + startd + " half=" + halfd + " halfh=" + halfh + " base=" + baseh + " rgb=" + r + "," + g + "," + b + " t=" + transition;
		/#
		PrintLn( line );
		#/
	}
	level.tod_fog_r = r;
	level.tod_fog_g = g;
	level.tod_fog_b = b;
	level.tod_fog_hh = halfh;
	level.tod_fog_hd = halfd;
	// NOTE: there is deliberately no level.tod_fog_op. Opacity is not a
	// SetVolFog argument at all (it lives in the fsi asset), so publishing one
	// would be recording a number this file does not control. The v14.37
	// version of this line read `= op` and survived only because `op` was then
	// a parameter; the v14.41 rename to `transition` turned it into a dangling
	// reference and the linker refused the whole file with "No generated data"
	// — which is the compile-kill this map's dialect note warns about, showing
	// up for a reason other than a misplaced #precache.
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
