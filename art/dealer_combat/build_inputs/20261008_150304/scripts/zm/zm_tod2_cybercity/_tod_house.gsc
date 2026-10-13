// THE DEALER'S HOUSE (docs/207, user 2026-10-04): the Battle Arena's last level is the final fight.
//
// "a separate arena that is even better and slightly bigger than existing one. This is the one
// players will get sent to on battle arena wave 10. The final fight. It starts off as player
// getting sent into a small box with the Black Market as the only thing in the center of room.
// Then a cut scene will start where the dealer starts talking to the players. And he ends up
// identifying himself as the evil mastermind ... he then teleports the players into the new
// battle arena and gets the players down to one HP with the same effect that the evil dome
// gives. Same visual so its a callback and scary since you have one health but you cant die.
// He talks a bit and then the boss fight starts ... the boss fight will only be him in his two
// phases" + "you need to build two more rooms for this" + "He lets you roll one last time and
// you get a very evil bad roll and he laughs like crazy. This is when he teleports you into the
// final fight".
//
// THE FLOW (run(), called by _tod_arena::arena_run in place of level 10's waves):
//   THE PARLOUR  the chamber's jump lands the party in a small box with the Black Market hut
//                at its centre (tools/dealer_house_layout.js). The music stops. The counter lights
//                (the shop's own parts, _tod_shop::house_shop_begin) and THE SCENE opens: every
//                player is frozen (the card panel's soft freeze: companions stop too), their view
//                locked on the mask behind the counter (a PlayerLinkToDelta mover with a little
//                room to breathe), the letterbox down (TodJumpCine's bars, kept alive past its
//                watchdog with the 3 beat). Four lines, 3D from the mask: who he is.
//   THE LAST ROLL the bars lift, the counter prompts ONE LAST ROLL (its own trigger: the normal
//                spin's two prompts stay off); the first player to hold USE rolls for everyone
//                (TOD_HOUSE_ROLL_WAIT, then he rolls for them). _tod_shop::house_roll runs the reel
//                on EVERY screen to a tile that is not on the wheel: CURSED. He gloats, then THE
//                LAUGH (the user: "he laughs like crazy"), the panel drops, "let me show you where
//                the money goes", and the teleporter's charge carries the party to THE HOUSE.
//   THE DRAIN    on the house's dais the haven's CORRUPTED dome rises round the party (the field
//                model at TOD_HOUSE_DOME_SCALE, its boot stutter, its dark hum, its red fx), every
//                screen takes the corrupted haven's red tint and darkness (the haven HUD's own
//                state, the callback the user asked for) and the health is cut to ONE in
//                TOD_HOUSE_DRAIN_STEPS bites (a flicker and a bite each) while he talks. Nobody
//                can die: a damage callback eats everything while level.tod_house_shield holds,
//                and the health is held at one under it (stock regen cannot climb).
//   THE FIGHT    he rises through his portal at the gate farthest from the party and waits (held:
//                level.tod_dealer_hold, read by _tod_dealer_finale::brain); on "the account is
//                open" the dome breaks, the darkness lifts, the freeze ends, the shield drops, the
//                readout reads THE FINAL FIGHT / THE DEALER, the boss track starts and he fights in
//                his two states (_tod_dealer_finale: the scythe float, then the cracked mask and the
//                gun at half health). His death is the level's win: _tod_arena::arena_win deals the
//                cards and rides the party home from the house's dais.
//   THE BARKS    (PK14, docs/199 s4) he is never silent between "the account is open", the crack
//                and his death: in state one a scythe hit he lands is called sometimes (the soft
//                register, swipe_bark from the damage guard), in state two he taunts the chase on a
//                clock (the manic register, bark_watch), and once, at a fifth of his health, the
//                composure cracks the other way (the low line). Every bark rides the same 2D lane,
//                waits for quiet, never repeats a line until its deck is spent, and yields: the
//                crack and the death line cut a bark still speaking (bark_yield).
//
// RULES: every wait here is a real wait (no world pause can start: the tower is held, the only
// card deal is the win's); every exit path lands in end() (the dome, the hum, the shield, the
// freeze, the hold, the trigger, the shop); the party is NEVER stranded (a Dealer who cannot
// spawn after TOD_HOUSE_SPAWN_TRIES is logged and the level is won without him); a line is one
// lane per player (his own, beside the shop's), timed from the GENERATED length table.
//
// Logs: [TOD_HOUSE] INIT / PARLOUR / CINE / LINE / ROLL / CURSED / LAUGH / SEND / HOUSE / DOME /
// CUT / ONE / SPAWN / FIGHT / DOWN / CRACK / DEALER_DOWN / END, each with the numbers behind it;
// the barks: BARKS (armed) / BARK (kind swipe|taunt|low) / SWIPE (every landed hit, its verdict) /
// TAUNT_CLOCK / BARK_YIELD.
// TOD_HOUSE_LOG prints with dev OFF for the user's playtest; ZERO before a publish.

#using scripts\shared\array_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm_laststand;
#using scripts\zm\_zm_utility;
#using scripts\zm\_zm_zonemgr;
#using scripts\zm\zm_tod2_cybercity\_tod_house_data;      // GENERATED: the two rooms' anchors
#using scripts\zm\zm_tod2_cybercity\_tod_teleport;        // fx_burst / discharge: the proven jump beats
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;    // play_sound_at_origin (the proven 3D lane)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_lights;     // set_glow: the mood light hosts
#using scripts\zm\zm_tod2_cybercity\_tod_upgrades;        // menu_freeze + pause_invuln_held_elsewhere
#using scripts\zm\zm_tod2_cybercity\_tod_shop;            // house_shop_begin / house_roll / house_roll_end / house_shop_end
#using scripts\zm\zm_tod2_cybercity\_tod_shop_vo;         // GENERATED: the length of every dealer line
#using scripts\zm\zm_tod2_cybercity\_tod_dealer_finale;   // spawn_boss: the Dealer himself
#using scripts\zm\zm_tod2_cybercity\_tod_atmosphere;      // channel_stop / arena_music_start

#insert scripts\shared\shared.gsh;

#precache( "model", "tod_haven_dome_dark" );
#precache( "model", "tod_haven_dome_dark_flash" );
#precache( "model", "tag_origin" );
#precache( "fx", "tod/haven/fx_tod_haven_corrupt" );
#precache( "fx", "tod/haven/fx_tod_haven_boot" );
#precache( "eventstring", "tod_house_cut" );   // THE DRAIN's flicker (TodHaven.lua, in the corrupted state)
#precache( "eventstring", "tod_haven" );       // the corrupted haven's tint + darkness (TodHaven.lua)
#precache( "eventstring", "tod_jump_cine" );   // the letterbox (TodJumpCine.lua): 1 in, 0 out, 3 keep

#namespace tod_house;

#define TOD_HOUSE_LOG             1      // prints with dev OFF for the user's playtest; ZERO before a publish
#define TOD_HOUSE_SETTLE_SECS     1.2    // after the landing in the parlour, before the scene opens
#define TOD_HOUSE_CINE_YAW        20     // the locked view may turn this far either side ...
#define TOD_HOUSE_CINE_PITCH      12     // ... and this far up / down (a cinematic that still breathes)
#define TOD_HOUSE_CINE_KEEP_SECS  8      // the letterbox's watchdog (17 s) is re-armed this often while the scene runs
#define TOD_HOUSE_LINE_GAP        0.45   // silence between two lines
#define TOD_HOUSE_ROLL_WAIT       25     // seconds the party has to take the last roll before he rolls for them
#define TOD_HOUSE_ROLL_READ_SECS  1.1    // the CURSED banner holds this long before his word
#define TOD_HOUSE_SEND_SECS       0.8    // the teleport's charge (the arena's TOD_ARENA_CHARGE_SECS)
#define TOD_HOUSE_DOME_SCALE      2.0    // the haven's field model this many times its size, over the dais
#define TOD_HOUSE_DOME_SPIN_SECS  36     // one revolution of its lattice
#define TOD_HOUSE_DRAIN_DELAY     2.0    // after the dome rises, before the first cut (he has started talking)
#define TOD_HOUSE_DRAIN_SECS      6.0    // the drain: full health -> one
#define TOD_HOUSE_DRAIN_STEPS     10     // cuts (a flicker + a bite each)
#define TOD_HOUSE_DRAIN_TICK      0.1    // the health is re-written this often (stock regen cannot climb under it)
#define TOD_HOUSE_ONE_HP          1      // "one health but you cant die"
#define TOD_HOUSE_SPAWN_TRIES     10     // spawn attempts for him (2 s apart) before the level is won without him
#define TOD_HOUSE_DOWN_VO_PCT     60     // a player going down during the fight gets his word this often
#define TOD_HOUSE_DOWN_VO_GAP     8      // ... and never twice in this many seconds
// THE BARKS (PK14): the lines are named in swipe_lines() / taunt_lines(); every knob below is one number
#define TOD_HOUSE_BARK_TICK       0.25   // the bark watcher's poll
#define TOD_HOUSE_BARK_GAP        6      // no bark starts within this many seconds of the end of the last bark ...
#define TOD_HOUSE_BARK_QUIET      2.5    // ... nor within this long of the end of ANY line of his (the down line, the crack)
#define TOD_HOUSE_SWIPE_VO_PCT    45     // a scythe hit he lands in state one is called this often ...
#define TOD_HOUSE_SWIPE_GAP       14     // ... and never twice in this many seconds (three lines: keep them fresh)
#define TOD_HOUSE_TAUNT_FIRST     6      // state two: the first taunt this many seconds after the crack line ends ...
#define TOD_HOUSE_TAUNT_MIN       14     // ... then one every MIN..MAX seconds while he lives
#define TOD_HOUSE_TAUNT_MAX       22
#define TOD_HOUSE_LOW_FRAC        0.2    // the low line, once, at this fraction of his health ...
#define TOD_HOUSE_LOW_QUIET       1.0    // ... after only this much quiet (it outranks a taunt and ignores the bark gap)
// W2B (PK10): his words wait for his sound - the crack line for the mask's crack + shriek (tod_dealer_mask_crack), the
// death line for the collapsing scream (tod_dealer_death, its rumble eased under the words from 1.0 s on)
#define TOD_HOUSE_CRACK_LINE_DELAY 0.7
#define TOD_HOUSE_DEATH_LINE_DELAY 1.0
#define TOD_HOUSE_MOOD_IDX        1      // the mood hosts' glow (todPerkGlow 1 = red: the arena's level-10 colour)
#define TOD_HOUSE_HUD_WAVE        1      // LOCKSTEP _tod_arena TOD_ARENA_HUD_WAVE: the fight's start flashes the readout
#define TOD_HOUSE_HINT_ROLL       "Hold ^3[{+activate}]^7 ^5BLACK MARKET^7 - the last roll / on the house - ^2FREE"
#define TOD_HOUSE_SND_HORN        "tod_arena_wave"        // the arena's horn: the fight begins
#define TOD_HOUSE_SND_IGNITE      "tod_haven_ignite"      // the dome rises (the haven's own)
#define TOD_HOUSE_SND_HUM         "tod_haven_hum_dark"    // the corrupted field's bed (looping, on the dome)
#define TOD_HOUSE_SND_DARK_IN     "tod_haven_dark_in"     // the darkness takes the screen (2D)
#define TOD_HOUSE_SND_BREAK       "tod_haven_wake"        // the dome breaks for the fight (the guardians' rise)
#define TOD_HOUSE_SND_DRAIN       "tod_house_drain"       // THE DRAIN's drone (2D, GENERATED tools/dealer_house/make_sounds.py)
#define TOD_HOUSE_SND_CUT         "tod_house_cut"         // one bite of it (2D)
#define TOD_HOUSE_FX_CORRUPT      "tod/haven/fx_tod_haven_corrupt"
#define TOD_HOUSE_FX_BOOT         "tod/haven/fx_tod_haven_boot"

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) && !TOD_HOUSE_LOG )
		return;
	line = "[TOD_HOUSE] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// ---------------------------------------------------------------------------
// INIT (called by _tod_arena::init)
// ---------------------------------------------------------------------------
function init()
{
	level.tod_house_shield = false;
	level.tod_house_cine = false;
	if ( !isdefined( level.player_damage_callbacks ) )
		level.player_damage_callbacks = [];
	ArrayInsert( level.player_damage_callbacks, &house_damage_guard, 0 );
	level.tod_dealer_crack_fn = &on_crack;   // _tod_dealer_finale: his mask cracks
	level.tod_dealer_death_fn = &on_death;   // _tod_dealer_finale: he dies
	dev_log( "INIT rev=1 parlour=" + tod_house_data::parlour_center() + " house=" + tod_house_data::house_center() + " dais=" + tod_house_data::house_dais()
		+ " drain_s=" + TOD_HOUSE_DRAIN_SECS + " steps=" + TOD_HOUSE_DRAIN_STEPS + " roll_wait=" + TOD_HOUSE_ROLL_WAIT + " dome_scale=" + TOD_HOUSE_DOME_SCALE );
}

function playing_players()
{
	out = [];
	foreach ( p in GetPlayers() )
		if ( isdefined( p ) && p.sessionstate == "playing" )
			out[ out.size ] = p;
	return out;
}

// PURE (tools/test_dealer_house.js runs these)
function shield_verdict( shield )
{
	return IS_TRUE( shield );
}

// the health a player holds after cut `step` of `steps`, from hp0: never above the line, never under one
function drain_target( hp0, step, steps )
{
	if ( steps < 1 )
		steps = 1;
	if ( step > steps )
		step = steps;
	t = int( hp0 - ( hp0 - TOD_HOUSE_ONE_HP ) * step / steps + 0.5 );
	if ( t < TOD_HOUSE_ONE_HP )
		t = TOD_HOUSE_ONE_HP;
	return t;
}

// the gate farthest from the party's centre: he comes in from across the pit
function farthest_gate( gates, orgs )
{
	if ( gates.size < 1 )
		return undefined;
	cx = 0;
	cy = 0;
	n = 0;
	foreach ( o in orgs )
	{
		cx += o[ 0 ];
		cy += o[ 1 ];
		n++;
	}
	if ( n < 1 )
		return gates[ 0 ];
	cx = cx / n;
	cy = cy / n;
	best = gates[ 0 ];
	best_d = -1;
	foreach ( g in gates )
	{
		d = ( g[ 0 ] - cx ) * ( g[ 0 ] - cx ) + ( g[ 1 ] - cy ) * ( g[ 1 ] - cy );
		if ( d > best_d )
		{
			best_d = d;
			best = g;
		}
	}
	return best;
}

// is this one of the house's 2D lines (the arena: his voice on every client), or a 3D one from the mask?
function line_is_2d( alias )
{
	return ( alias == "tod_house_vo_dome" || alias == "tod_house_vo_one" || alias == "tod_house_vo_fight"
		|| alias == "tod_house_vo_crack" || alias == "tod_house_vo_death" || alias == "tod_house_vo_down"
		|| alias == "tod_house_vo_swipe_1" || alias == "tod_house_vo_swipe_2" || alias == "tod_house_vo_swipe_3"
		|| alias == "tod_house_vo_taunt_1" || alias == "tod_house_vo_taunt_2" || alias == "tod_house_vo_taunt_3"
		|| alias == "tod_house_vo_taunt_4" || alias == "tod_house_vo_low" );
}

// THE BARKS' lines (PURE; the gate holds them to lines.json): the scythe calls (state one, the soft register) and the
// chase taunts (state two, the manic register). The low line is named where it is said (bark_watch).
function swipe_lines()
{
	return array( "tod_house_vo_swipe_1", "tod_house_vo_swipe_2", "tod_house_vo_swipe_3" );
}

function taunt_lines()
{
	return array( "tod_house_vo_taunt_1", "tod_house_vo_taunt_2", "tod_house_vo_taunt_3", "tod_house_vo_taunt_4" );
}

// PURE: the next line of a deck of n (an index): never one already said this cycle, never the one just said (a fresh
// cycle skips the last line of the one before). said = an array of n flags (unset = not said), r = any random int >= 0.
function deck_pick( said, n, last, r )
{
	free = [];
	for ( i = 0; i < n; i++ )
		if ( !IS_TRUE( said[ i ] ) )
			free[ free.size ] = i;
	if ( free.size < 1 )
		for ( i = 0; i < n; i++ )
			free[ free.size ] = i;
	if ( free.size > 1 && isdefined( last ) )
	{
		keep = [];
		foreach ( i in free )
			if ( i != last )
				keep[ keep.size ] = i;
		free = keep;
	}
	return free[ r % free.size ];
}

// PURE: may a bark start now? Never inside the bark gap (next_ms), never within quiet_ms of the end of a line still on
// any player's lane (untils = each playing player's tod_house_vo_until; an undefined entry is a free lane).
function bark_quiet( now, next_ms, untils, quiet_ms )
{
	if ( isdefined( next_ms ) && now < next_ms )
		return false;
	foreach ( u in untils )
		if ( isdefined( u ) && now < u + quiet_ms )
			return false;
	return true;
}

// PURE: one scythe hit he landed on a player -> "ok" (call it) or why not: state one only (the scythe; state two is the
// chase's taunts), never while he is held or the world is frozen, never on a hit that may down the player (the down line
// owns that moment), never inside TOD_HOUSE_SWIPE_GAP of the last call (now < next_ms), then the chance.
function swipe_verdict( state, held, hp, dmg, now, next_ms, roll )
{
	if ( state != 1 )
		return "state";
	if ( IS_TRUE( held ) )
		return "held";
	if ( dmg >= hp )
		return "lethal";
	if ( isdefined( next_ms ) && now < next_ms )
		return "gap";
	if ( roll >= TOD_HOUSE_SWIPE_VO_PCT )
		return "chance";
	return "ok";
}

// PURE: the low line is due once, while he lives, at or under TOD_HOUSE_LOW_FRAC of his health
function low_due( said, hp, maxhp )
{
	if ( IS_TRUE( said ) || maxhp <= 0 || hp <= 0 )
		return false;
	return ( hp <= maxhp * TOD_HOUSE_LOW_FRAC );
}

// level.player_damage_callbacks (self = the player): nothing lands while the shield holds. It is the chain's first
// listener in the house, so it is also where his landed scythe hits are heard (the swipe bark; never an opinion).
function house_damage_guard( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, psOffsetTime )
{
	if ( isdefined( eAttacker ) && IS_TRUE( eAttacker.tod_dealer ) && isdefined( level.tod_house_swipes ) && isdefined( sMeansOfDeath ) && sMeansOfDeath == "MOD_MELEE" )
		level thread swipe_bark( eAttacker, self, sMeansOfDeath, iDamage );
	if ( !shield_verdict( level.tod_house_shield ) )
		return -1;
	return 0;
}

function house_box()
{
	c = tod_house_data::house_center();
	h = tod_house_data::house_half();
	b = SpawnStruct();
	b.x1 = c[ 0 ] - h; b.x2 = c[ 0 ] + h;
	b.y1 = c[ 1 ] - h; b.y2 = c[ 1 ] + h;
	b.z1 = c[ 2 ] - 64; b.z2 = tod_house_data::house_top();
	b.tod_arena = true;   // _tod_arena::arena_win clears a box it owns
	return b;
}

// ---------------------------------------------------------------------------
// THE VOICE: his own lane per player beside the shop's, timed from the GENERATED table
// ---------------------------------------------------------------------------
// one line to one player: a 2D line on their client, a 3D one from the mask behind the counter
function say_to( p, alias )
{
	if ( !isdefined( p ) || !isplayer( p ) )
		return false;
	now = GetTime();
	if ( isdefined( p.tod_house_vo_until ) && now < p.tod_house_vo_until )
	{
		dev_log( "VO_DROP player=" + p GetEntityNumber() + " alias=" + alias + " busy_ms=" + ( p.tod_house_vo_until - now ) );
		return false;
	}
	secs = tod_shop_vo::secs( alias );
	p.tod_house_vo_until = now + int( secs * 1000 ) + int( TOD_HOUSE_LINE_GAP * 1000 );
	p.tod_house_bark = undefined;   // this lane holds a story line now (bark_play marks its own after this returns)
	if ( line_is_2d( alias ) )
		p PlayLocalSound( alias );
	else
	{
		mouth = tod_shop::house_mouth();
		if ( !isdefined( mouth ) )
			p PlayLocalSound( alias );
		else
			mouth PlaySoundToPlayer( alias, p );
	}
	return true;
}

// the line to every playing player, then its length (+ the gap) waited out
function say_all( alias )
{
	n = 0;
	foreach ( p in playing_players() )
		if ( say_to( p, alias ) )
			n++;
	secs = tod_shop_vo::secs( alias );
	dev_log( "LINE alias=" + alias + " secs=" + secs + " hearers=" + n );
	wait secs + TOD_HOUSE_LINE_GAP;
}

// the same, without the wait (a thread)
function say_all_now( alias )
{
	n = 0;
	foreach ( p in playing_players() )
		if ( say_to( p, alias ) )
			n++;
	dev_log( "LINE alias=" + alias + " secs=" + tod_shop_vo::secs( alias ) + " hearers=" + n + " (threaded)" );
}

// ---------------------------------------------------------------------------
// THE RUN. -> true when the fight is won (or he never came: never strand the party), false when
// the rooms could not open (the caller refunds and releases; nobody has moved).
// ---------------------------------------------------------------------------
function run( lvl, op )
{
	level endon( "end_game" );
	pz = tod_house_data::parlour_zone();
	hz = tod_house_data::house_zone();
	if ( !isdefined( level.zones[ pz ] ) || !isdefined( level.zones[ hz ] ) )
	{
		dev_log( "ABORT reason=no_zone parlour=" + isdefined( level.zones[ pz ] ) + " house=" + isdefined( level.zones[ hz ] ) );
		return false;
	}
	zm_zonemgr::enable_zone( pz );
	zm_zonemgr::enable_zone( hz );
	level.zones[ pz ].is_spawning_allowed = false;   // nothing ever rises here but him
	level.zones[ hz ].is_spawning_allowed = false;
	level.tod_trial_box = house_box();
	level.tod_arena_active = true;
	level.tod_arena_depart = tod_house_data::house_dais();   // _tod_arena::arena_win rides home from here
	if ( isdefined( level.tod_arena_hud ) )
	{
		level.tod_arena_hud.show = false;   // the readout waits for the fight
		level.tod_arena_hud.house = true;
	}
	hud( 0 );
	if ( isdefined( level.tod_arena_hud_watch_fn ) )
		level thread [[ level.tod_arena_hud_watch_fn ]]();   // the arena's 2 s re-send (it ends with the fight)
	// the downed stand up: nobody misses the scene
	foreach ( p in playing_players() )
		if ( p laststand::player_is_in_laststand() )
			p thread zm_laststand::auto_revive( p );
	parlour( lvl, op );
	dome_and_drain();
	won = fight();
	end();
	return won;
}

// the arena's readout, through its own push (the flags are its LOCKSTEP bits)
function hud( flags )
{
	if ( isdefined( level.tod_arena_hud_push_fn ) )
		[[ level.tod_arena_hud_push_fn ]]( flags );
}

// ---------------------------------------------------------------------------
// THE PARLOUR
// ---------------------------------------------------------------------------
function parlour( lvl, op )
{
	level endon( "end_game" );
	arr = tod_house_data::parlour_arrivals();
	yaw = tod_house_data::parlour_arrival_yaw();
	center = tod_house_data::parlour_center();
	front = center + ( 0, -200, 0 );
	// THE JUMP (the chamber's discharge fired in the caller's frame): the move, then two frames on the
	// arrival flash (the transit pads' rule: the host replicates after the riders)
	party = playing_players();
	for ( i = 0; i < party.size; i++ )
	{
		party[ i ] SetOrigin( arr[ i % arr.size ] );
		party[ i ] SetPlayerAngles( ( 0, yaw, 0 ) );
		party[ i ].tod_arena_fall_logged = undefined;
	}
	level.tod_tp_stamp = ( isdefined( level.tod_tp_stamp ) ? level.tod_tp_stamp + 1 : 1 );
	WAIT_SERVER_FRAME;
	WAIT_SERVER_FRAME;
	level thread tod_teleport::fx_burst( "tod_tp_kino", front + ( 0, 0, 4 ), 3.0 );
	tod_teleport::discharge( front );
	tod_atmosphere::channel_stop();   // silence: his voice and the hut own the room
	ok = tod_shop::house_shop_begin( tod_house_data::parlour_shop_org(), tod_house_data::parlour_shop_yaw() );
	dev_log( "PARLOUR level=" + lvl + " party=" + party.size + " shop=" + ok + " ms_since_use=" + ( GetTime() - op ) );
	wait TOD_HOUSE_SETTLE_SECS;

	// THE SCENE
	level.tod_house_cine = true;
	foreach ( p in playing_players() )
		p cine_begin();
	level thread cine_keepalive();
	wait 0.6;
	say_all( "tod_house_vo_welcome" );
	level thread counter_sparks( 1.6, 2 );
	say_all( "tod_house_vo_ledger" );
	level thread counter_sparks( 0.8, 3 );
	say_all( "tod_house_vo_reveal" );
	say_all( "tod_house_vo_offer" );
	level.tod_house_cine = false;
	foreach ( p in GetPlayers() )
		if ( isdefined( p ) && isplayer( p ) )
			p cine_end();

	// THE LAST ROLL
	roller = roll_wait();
	if ( !isdefined( roller ) )
		say_all( "tod_house_vo_too_slow" );
	party = playing_players();
	foreach ( p in party )
		p tod_upgrades::menu_freeze( true );   // everyone watches; nobody wanders off
	t0 = GetTime();
	tod_shop::house_roll( roller, party );    // the reel to CURSED on every screen; returns at the landing
	dev_log( "CURSED roller=" + ( isdefined( roller ) ? roller GetEntityNumber() : -1 ) + " reel_ms=" + ( GetTime() - t0 ) + " party=" + party.size );
	wait TOD_HOUSE_ROLL_READ_SECS;
	say_all( "tod_house_vo_cursed" );
	// THE LAUGH, over the cursed banner: the counter sparks and blasts under it, the room shakes
	secs = tod_shop_vo::secs( "tod_house_vo_laugh" );
	level thread counter_sparks( 0.4, 5 );
	Earthquake( 0.22, secs, tod_house_data::parlour_shop_org(), 900 );
	dev_log( "LAUGH secs=" + secs );
	say_all( "tod_house_vo_laugh" );
	tod_shop::house_roll_end( party );        // the panel drops
	wait 0.4;
	// THE SEND: the charge rides his line, the jump lands in dome_and_drain()
	charge_org = tod_house_data::parlour_counter() + ( 0, 0, 20 );
	level thread say_all_now( "tod_house_vo_send" );
	wait Max( 0.0, tod_shop_vo::secs( "tod_house_vo_send" ) - TOD_HOUSE_SEND_SECS );
	level thread tod_teleport::fx_burst( "tod_tp_charge", charge_org, TOD_HOUSE_SEND_SECS + 0.5, "tod_tp_charge_field" );
	tod_perk_scatter::play_sound_at_origin( charge_org, "tod_teleport_fire", 4 );
	dev_log( "SEND charge_s=" + TOD_HOUSE_SEND_SECS );
	wait TOD_HOUSE_SEND_SECS;
	tod_teleport::discharge( charge_org );
}

// the mask's eyes and the counter crackle under a line: n short spark bursts, the first after `delay`
function counter_sparks( delay, n )
{
	level endon( "end_game" );
	wait delay;
	counter = tod_house_data::parlour_shop_org() + ( 0, -50, 60 );
	for ( i = 0; i < n; i++ )
	{
		tod_perk_scatter::play_sound_at_origin( counter, "tod_shop_spark_" + ( RandomInt( 3 ) + 1 ), 4 );
		level thread tod_shop::fx_burst( "electric/fx_elec_spark_loop_sm", counter, 0.5 );
		wait RandomFloatRange( 0.5, 1.1 );
	}
}

// self = a player: frozen (weapons down, feet pinned, the companion stops), the view locked on the mask
// with a little room to breathe, the letterbox down
function cine_begin()
{
	if ( !isdefined( self ) || !isplayer( self ) || self laststand::player_is_in_laststand() )
		return;
	self.tod_house_cine = true;
	self tod_upgrades::menu_freeze( true );
	self HideViewModel();
	mouth = tod_shop::house_mouth();
	look = tod_house_data::parlour_shop_org() + ( 0, 12, 70 );
	if ( isdefined( mouth ) )
		look = mouth.origin;
	ang = VectorToAngles( look - self GetEye() );
	ang = ( ang[ 0 ], ang[ 1 ], 0 );
	mover = Spawn( "script_model", self.origin );
	if ( isdefined( mover ) )
	{
		mover SetModel( "tag_origin" );
		mover.angles = ang;
		self SetPlayerAngles( ang );
		self PlayerLinkToDelta( mover, "tag_origin", 1, TOD_HOUSE_CINE_YAW, TOD_HOUSE_CINE_YAW, TOD_HOUSE_CINE_PITCH, TOD_HOUSE_CINE_PITCH );
		self.tod_house_mover = mover;
	}
	self LuiNotifyEvent( &"tod_jump_cine", 1, 1 );
	dev_log( "CINE player=" + self GetEntityNumber() + " on angles=" + ang + " linked=" + isdefined( mover ) );
}

// self = a player: everything cine_begin did, undone (idempotent)
function cine_end()
{
	if ( !IS_TRUE( self.tod_house_cine ) )
		return;
	self.tod_house_cine = undefined;
	if ( isdefined( self.tod_house_mover ) )
	{
		self Unlink();
		self.tod_house_mover Delete();
		self.tod_house_mover = undefined;
	}
	self ShowViewModel();
	self tod_upgrades::menu_freeze( false );
	self LuiNotifyEvent( &"tod_jump_cine", 1, 0 );
	dev_log( "CINE player=" + self GetEntityNumber() + " off" );
}

// the letterbox's watchdog drops the bars after 17 s on its own: the 3 beat re-arms it while the scene runs
function cine_keepalive()
{
	level endon( "end_game" );
	while ( IS_TRUE( level.tod_house_cine ) )
	{
		wait TOD_HOUSE_CINE_KEEP_SECS;
		if ( !IS_TRUE( level.tod_house_cine ) )
			return;
		foreach ( p in GetPlayers() )
			if ( isdefined( p ) && isplayer( p ) && IS_TRUE( p.tod_house_cine ) )
				p LuiNotifyEvent( &"tod_jump_cine", 1, 3 );
	}
}

// THE LAST ROLL's prompt: a use trigger before the counter for TOD_HOUSE_ROLL_WAIT. -> the player who
// took it, or undefined (he rolls for them)
function roll_wait()
{
	level endon( "end_game" );
	level.tod_house_roller = undefined;
	t = Spawn( "trigger_radius_use", tod_house_data::parlour_counter(), 0, 64, 72 );
	if ( !isdefined( t ) )
	{
		dev_log( "ROLL trigger_spawn_failed (he rolls for them)" );
		wait 2.0;
		return undefined;
	}
	t TriggerIgnoreTeam();
	t SetCursorHint( "HINT_NOICON" );
	t SetHintString( TOD_HOUSE_HINT_ROLL );
	level.tod_house_roll_trig = t;
	foreach ( p in playing_players() )
		p IPrintLnBold( "ONE LAST ROLL - ON THE HOUSE" );
	level thread roll_trigger_watch( t );
	level util::waittill_any_timeout( TOD_HOUSE_ROLL_WAIT, "tod_house_rolled" );
	roller = level.tod_house_roller;
	level.tod_house_roll_trig = undefined;
	t Delete();
	dev_log( "ROLL roller=" + ( isdefined( roller ) ? roller GetEntityNumber() : -1 ) + " waited_max=" + TOD_HOUSE_ROLL_WAIT );
	return roller;
}

function roll_trigger_watch( t )
{
	level endon( "end_game" );
	level endon( "tod_house_rolled" );
	t endon( "death" );
	while ( true )
	{
		t waittill( "trigger", p );
		if ( !isdefined( p ) || !isplayer( p ) || !zm_utility::is_player_valid( p ) )
			continue;
		if ( p laststand::player_is_in_laststand() )
			continue;
		level.tod_house_roller = p;
		level notify( "tod_house_rolled" );
		return;
	}
}

// ---------------------------------------------------------------------------
// THE HOUSE: the dome and the drain
// ---------------------------------------------------------------------------
function dome_and_drain()
{
	level endon( "end_game" );
	land = tod_house_data::house_arrivals();
	dais = tod_house_data::house_dais();
	party = playing_players();
	for ( i = 0; i < party.size; i++ )
	{
		dst = land[ i % land.size ];
		face = VectorToAngles( dst - dais );
		party[ i ] SetOrigin( dst );
		party[ i ] SetPlayerAngles( ( 0, face[ 1 ], 0 ) );
		party[ i ].tod_arena_fall_logged = undefined;
		party[ i ] tod_upgrades::menu_freeze( true );   // the dome's moment is not a fight yet
	}
	level.tod_tp_stamp = ( isdefined( level.tod_tp_stamp ) ? level.tod_tp_stamp + 1 : 1 );
	WAIT_SERVER_FRAME;
	WAIT_SERVER_FRAME;
	level thread tod_teleport::fx_burst( "tod_tp_kino", dais + ( 0, 0, 4 ), 3.0 );
	tod_teleport::discharge( dais );
	dev_log( "HOUSE party=" + party.size + " dais=" + dais );
	wait 0.6;

	// THE DOME: the corrupted haven's field, its boot stutter, its hum, its red
	dome = Spawn( "script_model", dais );
	if ( isdefined( dome ) )
	{
		dome SetModel( "tod_haven_dome_dark_flash" );
		dome SetScale( TOD_HOUSE_DOME_SCALE );
		dome.angles = ( 0, 0, 0 );
		dome NotSolid();
		dome Hide();
		level.tod_house_dome = dome;
		wait 0.05;
		fx_at( TOD_HOUSE_FX_BOOT, dais, 3 );
		dome PlaySound( TOD_HOUSE_SND_IGNITE );
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
		dome PlayLoopSound( TOD_HOUSE_SND_HUM, 1 );
		dome thread dome_spin();
		level.tod_house_fx = fx_host( TOD_HOUSE_FX_CORRUPT, dais );
	}
	else
		dev_log( "SPAWN_FAILED dome (entity pool full): the drain runs without it" );

	// THE DARKNESS on every screen (the corrupted haven's own state) and the shield: nobody can die
	level.tod_house_shield = true;
	foreach ( p in playing_players() )
	{
		p EnableInvulnerability();
		p.tod_house_dark = true;
		p LuiNotifyEvent( &"tod_haven", 4, 1, 0, 1, 0 );
		p PlayLocalSound( TOD_HOUSE_SND_DARK_IN );
	}
	dev_log( "DOME scale=" + TOD_HOUSE_DOME_SCALE + " shield=1 party=" + playing_players().size );
	level thread say_all_now( "tod_house_vo_dome" );
	wait TOD_HOUSE_DRAIN_DELAY;
	drain();
	level thread hold_one();
	say_all( "tod_house_vo_one" );
}

// THE DRAIN: everyone's health down to one in TOD_HOUSE_DRAIN_STEPS cuts over TOD_HOUSE_DRAIN_SECS, the
// line held between cuts every tick (stock regen cannot climb under it), a flicker and a bite per cut
function drain()
{
	level endon( "end_game" );
	foreach ( p in playing_players() )
	{
		hp = p.health;
		if ( !isdefined( hp ) || hp < 1 )
			hp = p.maxhealth;
		p.tod_house_hp0 = hp;
		p PlayLocalSound( TOD_HOUSE_SND_DRAIN );
	}
	ticks = int( TOD_HOUSE_DRAIN_SECS / TOD_HOUSE_DRAIN_STEPS / TOD_HOUSE_DRAIN_TICK + 0.5 );
	if ( ticks < 1 )
		ticks = 1;
	for ( s = 1; s <= TOD_HOUSE_DRAIN_STEPS; s++ )
	{
		for ( k = 0; k < ticks; k++ )
		{
			foreach ( p in playing_players() )
				hold_at( p, s - 1 );
			wait TOD_HOUSE_DRAIN_TICK;
		}
		// THE CUT
		n = 0;
		foreach ( p in playing_players() )
		{
			if ( !isdefined( p.tod_house_hp0 ) )
				p.tod_house_hp0 = p.maxhealth;
			t = drain_target( p.tod_house_hp0, s, TOD_HOUSE_DRAIN_STEPS );
			if ( p.health > t )
				p.health = t;
			p LuiNotifyEvent( &"tod_house_cut", 1, 1 );
			p PlayLocalSound( TOD_HOUSE_SND_CUT );
			n++;
		}
		dev_log( "CUT step=" + s + "/" + TOD_HOUSE_DRAIN_STEPS + " players=" + n );
	}
	dev_log( "ONE every player at " + TOD_HOUSE_ONE_HP + " hp" );
}

// never above the line of the last cut (a downed player is left alone: stock owns last stand)
function hold_at( p, step )
{
	if ( !isdefined( p ) || !isplayer( p ) || !IsAlive( p ) || p laststand::player_is_in_laststand() )
		return;
	if ( !isdefined( p.tod_house_hp0 ) )
		return;
	t = drain_target( p.tod_house_hp0, step, TOD_HOUSE_DRAIN_STEPS );
	if ( p.health > t )
		p.health = t;
}

// after the drain, until the fight starts: everyone stays at one
function hold_one()
{
	level endon( "end_game" );
	level endon( "tod_house_release" );
	while ( true )
	{
		foreach ( p in playing_players() )
			hold_at( p, TOD_HOUSE_DRAIN_STEPS );
		wait TOD_HOUSE_DRAIN_TICK;
	}
}

function dome_spin()   // self = the dome
{
	self endon( "death" );
	level endon( "end_game" );
	for ( ;; )
	{
		self RotateYaw( 360, TOD_HOUSE_DOME_SPIN_SECS );
		self waittill( "rotatedone" );
	}
}

// the dome breaks for the fight: the haven's cleanse stutter, the guardians' rise, gone
function dome_break()
{
	level endon( "end_game" );
	dome = level.tod_house_dome;
	level.tod_house_dome = undefined;
	if ( isdefined( level.tod_house_fx ) )
		level.tod_house_fx Delete();
	level.tod_house_fx = undefined;
	if ( !isdefined( dome ) )
		return;
	dome StopLoopSound( 0.3 );
	dome PlaySound( TOD_HOUSE_SND_BREAK );
	steps = array( 0.06, 0.08, 0.05, 0.10, 0.06, 0.12 );
	for ( i = 0; i < steps.size; i++ )
	{
		if ( !isdefined( dome ) )
			return;
		dome SetModel( ( ( i % 2 == 0 ) ? "tod_haven_dome_dark_flash" : "tod_haven_dome_dark" ) );
		wait steps[ i ];
	}
	if ( isdefined( dome ) )
		dome Delete();
}

// ---------------------------------------------------------------------------
// THE FIGHT: him, in his two states, to the death. -> true (the win; also when he never came)
// ---------------------------------------------------------------------------
function fight()
{
	level endon( "end_game" );
	party = playing_players();
	orgs = [];
	foreach ( p in party )
		orgs[ orgs.size ] = p.origin;
	gate = farthest_gate( tod_house_data::house_gates(), orgs );
	if ( !isdefined( gate ) )
		gate = tod_house_data::house_center();
	target = ArrayGetClosest( gate, party );
	level.tod_dealer_hold = true;   // he rises and waits while he talks
	dealer = undefined;
	for ( tries = 0; tries < TOD_HOUSE_SPAWN_TRIES && !isdefined( dealer ); tries++ )
	{
		dealer = tod_dealer_finale::spawn_boss( gate, target );
		if ( !isdefined( dealer ) )
		{
			dev_log( "SPAWN_RETRY try=" + ( tries + 1 ) + " free_actors=" + GetFreeActorCount() );
			wait 2.0;
		}
	}
	if ( !isdefined( dealer ) )
	{
		// never strand the party: the level is won without him (the log says so, loudly)
		dev_log( "DEALER_NOSHOW tries=" + TOD_HOUSE_SPAWN_TRIES + " free_actors=" + GetFreeActorCount() + " (the level is won without the fight)" );
		level thread dome_break();
		foreach ( p in playing_players() )
			darkness_off( p );
		release();
		return true;
	}
	dealer.tod_arena = true;
	level.tod_arena_ai = array::remove_undefined( level.tod_arena_ai );
	level.tod_arena_ai[ level.tod_arena_ai.size ] = dealer;
	if ( isdefined( level.tod_arena_hud ) )
	{
		level.tod_arena_hud.boss = dealer;
		level.tod_arena_hud.total = 1;
		level.tod_arena_hud.risen = 1;
	}
	dev_log( "SPAWN ent=" + dealer GetEntityNumber() + " hp=" + dealer.health + " at=" + gate + " held=1" );
	wait 1.5;   // his portal's float-in

	// "the account is open": the dome breaks and the darkness lifts under the line, the fight starts at its end
	level thread dome_break();
	foreach ( p in playing_players() )
		darkness_off( p );
	say_all( "tod_house_vo_fight" );
	release();
	if ( isdefined( level.tod_arena_hud ) )
		level.tod_arena_hud.show = true;
	hud( TOD_HOUSE_HUD_WAVE );
	foreach ( p in playing_players() )
		p PlaySoundToPlayer( TOD_HOUSE_SND_HORN, p );
	tod_atmosphere::arena_music_start();
	level thread mood_on();
	dev_log( "FIGHT ent=" + dealer GetEntityNumber() + " hp=" + dealer.health + " party=" + playing_players().size );
	level thread down_watch( dealer );
	level thread bark_watch( dealer );
	while ( isdefined( dealer ) && IsAlive( dealer ) )
		wait 0.5;
	dev_log( "DEALER_DOWN" );
	wait ( TOD_HOUSE_DEATH_LINE_DELAY + tod_shop_vo::secs( "tod_house_vo_death" ) + 0.25 );   // his full last word before the reward screen
	dev_log( "DEATH_LINE_COMPLETE" );
	return true;
}

// self-less: the shield, the freeze, the hold and the one-health line let go in one place
function release()
{
	level.tod_house_shield = false;
	level.tod_dealer_hold = false;
	level notify( "tod_house_release" );
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || !isplayer( p ) )
			continue;
		p tod_upgrades::menu_freeze( false );
		if ( !IS_TRUE( p.tod_pause_invuln ) && !IS_TRUE( p.tod_spin_locked ) && !( p tod_upgrades::pause_invuln_held_elsewhere() ) )
			p DisableInvulnerability();
		p.tod_house_hp0 = undefined;
	}
	dev_log( "RELEASE shield=0 hold=0" );
}

// the corrupted tint and darkness leave the screen (a crossing pulse, like leaving a field)
function darkness_off( p )
{
	if ( !isdefined( p ) || !isplayer( p ) || !IS_TRUE( p.tod_house_dark ) )
		return;
	p.tod_house_dark = undefined;
	p LuiNotifyEvent( &"tod_haven", 4, 0, 1, 0, 0 );
}

// a player going down during the fight: his word, sometimes, never twice in TOD_HOUSE_DOWN_VO_GAP
function down_watch( dealer )
{
	level endon( "end_game" );
	level endon( "tod_house_over" );
	was = [];
	next = 0;
	while ( isdefined( dealer ) && IsAlive( dealer ) )
	{
		wait 0.5;
		foreach ( p in playing_players() )
		{
			n = p GetEntityNumber();
			down = p laststand::player_is_in_laststand();
			if ( down && !IS_TRUE( was[ n ] ) && GetTime() >= next )
			{
				dev_log( "DOWN player=" + n );
				if ( RandomInt( 100 ) < TOD_HOUSE_DOWN_VO_PCT )
				{
					level thread say_all_now( "tod_house_vo_down" );
					next = GetTime() + TOD_HOUSE_DOWN_VO_GAP * 1000;
				}
			}
			was[ n ] = down;
		}
	}
}

// _tod_dealer_finale's hooks (level.tod_dealer_crack_fn / _death_fn): his word at the crack and at the end
function on_crack( dealer )
{
	dev_log( "CRACK ent=" + ( isdefined( dealer ) ? dealer GetEntityNumber() : -1 ) + " line_in=" + TOD_HOUSE_CRACK_LINE_DELAY );
	bark_yield( "crack" );   // the crack is never dropped behind a scythe call still speaking
	level thread story_line_after( "tod_house_vo_crack", TOD_HOUSE_CRACK_LINE_DELAY, "crack" );
}

function on_death( dealer )
{
	dev_log( "DEATH ent=" + ( isdefined( dealer ) ? dealer GetEntityNumber() : -1 ) );
	level.tod_house_swipes = undefined;   // the barks are over with him
	bark_yield( "death" );   // his last word is never dropped behind a taunt or the low line
	level thread story_line_after( "tod_house_vo_death", TOD_HOUSE_DEATH_LINE_DELAY, "death" );
}

// W2B (PK10): the crack and the death each open on his SOUND (the mask's crack and shriek, the collapsing scream,
// _tod_dealer_finale), so his words come a beat after it instead of over it; whatever bark started in that beat is cut
function story_line_after( alias, secs, why )
{
	level endon( "end_game" );
	wait secs;
	bark_yield( why );
	say_all_now( alias );
}

// ---------------------------------------------------------------------------
// THE BARKS (PK14, docs/199 s4): his voice between the opening line, the crack and his death
// ---------------------------------------------------------------------------
// a deck of lines: each said once before any repeats, never the same line twice running
function deck_new( lines )
{
	d = SpawnStruct();
	d.lines = lines;
	d.said = [];
	d.last = undefined;
	return d;
}

function deck_draw( d )
{
	left = 0;
	for ( i = 0; i < d.lines.size; i++ )
		if ( !IS_TRUE( d.said[ i ] ) )
			left++;
	if ( left < 1 )
		d.said = [];   // a new cycle (deck_pick still skips the line just said)
	k = deck_pick( d.said, d.lines.size, d.last, RandomInt( 1000 ) );
	d.said[ k ] = true;
	d.last = k;
	return d.lines[ k ];
}

// every playing player's lane end (deck_pick's quiet test)
function lanes()
{
	out = [];
	foreach ( p in playing_players() )
		if ( isdefined( p.tod_house_vo_until ) )
			out[ out.size ] = p.tod_house_vo_until;
	return out;
}

// one bark to everyone on the lane (2D: his voice in the room), marked so a story line can cut it
function bark_play( alias, kind, dealer )
{
	n = 0;
	foreach ( p in playing_players() )
	{
		if ( say_to( p, alias ) )
		{
			p.tod_house_bark = alias;
			n++;
		}
	}
	secs = tod_shop_vo::secs( alias );
	level.tod_house_bark_next = GetTime() + int( ( secs + TOD_HOUSE_BARK_GAP ) * 1000 );
	pct = -1;
	state = -1;
	if ( isdefined( dealer ) && isdefined( dealer.maxhealth ) && dealer.maxhealth > 0 )
	{
		pct = int( 100 * dealer.health / dealer.maxhealth );
		state = dealer.tod_dealer_state;
	}
	dev_log( "BARK kind=" + kind + " alias=" + alias + " secs=" + secs + " hearers=" + n + " hp_pct=" + pct + " state=" + state );
	return n;
}

// a story line (the crack, the death) cuts any bark still speaking and frees its lane
function bark_yield( why )
{
	now = GetTime();
	n = 0;
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || !isplayer( p ) || !isdefined( p.tod_house_bark ) )
			continue;
		if ( isdefined( p.tod_house_vo_until ) && now < p.tod_house_vo_until )
		{
			p StopLocalSound( p.tod_house_bark );
			p.tod_house_vo_until = undefined;
			n++;
		}
		p.tod_house_bark = undefined;
	}
	if ( n > 0 )
		dev_log( "BARK_YIELD for=" + why + " cut=" + n );
}

// THE SCYTHE CALLS (state one): house_damage_guard hears every hit he lands and hands it here (self-less, no wait)
function swipe_bark( dealer, victim, mod, dmg )
{
	if ( !isdefined( dealer ) || !isdefined( victim ) || !isplayer( victim ) || !isdefined( level.tod_house_swipes ) )
		return;
	if ( !isdefined( mod ) )
		mod = "none";
	if ( !isdefined( dmg ) )
		dmg = 0;
	held = ( IS_TRUE( level.tod_dealer_hold ) || IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( level.tod_house_shield ) );
	now = GetTime();
	why = swipe_verdict( dealer.tod_dealer_state, held, victim.health, dmg, now, level.tod_house_swipe_next, RandomInt( 100 ) );
	if ( why == "ok" && victim laststand::player_is_in_laststand() )
		why = "down";
	if ( why == "ok" && !bark_quiet( now, level.tod_house_bark_next, lanes(), int( TOD_HOUSE_BARK_QUIET * 1000 ) ) )
		why = "busy";
	dev_log( "SWIPE victim=" + victim GetEntityNumber() + " mod=" + mod + " dmg=" + dmg + " hp=" + victim.health + " state=" + dealer.tod_dealer_state + " verdict=" + why );
	if ( why != "ok" )
		return;
	level.tod_house_swipe_next = now + TOD_HOUSE_SWIPE_GAP * 1000;
	bark_play( deck_draw( level.tod_house_swipes ), "swipe", dealer );
}

// THE CHASE (state two) + THE LOW LINE: one watcher for the fight's clock-driven barks
function bark_watch( dealer )
{
	level endon( "end_game" );
	level endon( "tod_house_over" );
	level.tod_house_bark_next = 0;
	level.tod_house_swipe_next = 0;
	level.tod_house_swipes = deck_new( swipe_lines() );
	taunts = deck_new( taunt_lines() );
	low_said = false;
	taunt_at = undefined;
	dev_log( "BARKS armed swipes=" + swipe_lines().size + " taunts=" + taunt_lines().size + " swipe_pct=" + TOD_HOUSE_SWIPE_VO_PCT
		+ " taunt_s=" + TOD_HOUSE_TAUNT_MIN + ".." + TOD_HOUSE_TAUNT_MAX + " low_frac=" + TOD_HOUSE_LOW_FRAC );
	while ( isdefined( dealer ) && IsAlive( dealer ) )
	{
		wait TOD_HOUSE_BARK_TICK;
		if ( !isdefined( dealer ) || !IsAlive( dealer ) )
			break;
		if ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( level.tod_dealer_hold ) )
			continue;
		now = GetTime();
		// THE LOW LINE: once, the moment there is a breath of quiet (it outranks a taunt; the bark gap does not hold it)
		if ( low_due( low_said, dealer.health, dealer.maxhealth ) )
		{
			if ( bark_quiet( now, undefined, lanes(), int( TOD_HOUSE_LOW_QUIET * 1000 ) ) )
			{
				low_said = true;
				bark_play( "tod_house_vo_low", "low", dealer );
			}
			continue;
		}
		if ( dealer.tod_dealer_state != 2 )
			continue;
		// THE CHASE: the clock starts at the crack (its line, then TOD_HOUSE_TAUNT_FIRST of breath)
		if ( !isdefined( taunt_at ) )
		{
			taunt_at = now + int( ( TOD_HOUSE_CRACK_LINE_DELAY + tod_shop_vo::secs( "tod_house_vo_crack" ) + TOD_HOUSE_TAUNT_FIRST ) * 1000 );
			dev_log( "TAUNT_CLOCK first_in_ms=" + ( taunt_at - now ) );
			continue;
		}
		if ( now >= taunt_at && bark_quiet( now, level.tod_house_bark_next, lanes(), int( TOD_HOUSE_BARK_QUIET * 1000 ) ) )
		{
			bark_play( deck_draw( taunts ), "taunt", dealer );
			taunt_at = now + RandomIntRange( TOD_HOUSE_TAUNT_MIN, TOD_HOUSE_TAUNT_MAX + 1 ) * 1000;
		}
	}
}

// ---------------------------------------------------------------------------
// THE MOOD LIGHTS (the arena's lane): the four pylon collars and the dais, red for the fight
// ---------------------------------------------------------------------------
function mood_on()
{
	level endon( "end_game" );
	mood_off();
	hosts = [];
	foreach ( o in tod_house_data::house_mood_orgs() )
	{
		h = Spawn( "script_model", o );
		if ( !isdefined( h ) )
			continue;
		h SetModel( "tag_origin" );
		hosts[ hosts.size ] = h;
	}
	level.tod_house_mood = hosts;
	wait 0.1;   // a snapshot: the client lane resolves tag_origin on the entity's dobj (the power wave's rule)
	foreach ( h in hosts )
		if ( isdefined( h ) )
			tod_perk_lights::set_glow( h, TOD_HOUSE_MOOD_IDX );
	dev_log( "MOOD hosts=" + hosts.size + " index=" + TOD_HOUSE_MOOD_IDX );
}

function mood_off()
{
	if ( !isdefined( level.tod_house_mood ) )
		return;
	hosts = level.tod_house_mood;
	level.tod_house_mood = undefined;
	foreach ( h in hosts )
		if ( isdefined( h ) )
			tod_perk_lights::set_glow( h, 0 );
	level thread delete_hosts( hosts, 0.5 );
}

function delete_hosts( hosts, secs )
{
	wait secs;
	foreach ( h in hosts )
		if ( isdefined( h ) )
			h Delete();
}

// ---------------------------------------------------------------------------
// THE END: every exit path (the win, a no-show) lands here before the arena rides the party home
// ---------------------------------------------------------------------------
function end()
{
	level notify( "tod_house_over" );
	level.tod_dealer_hold = undefined;
	level.tod_house_shield = false;
	level.tod_house_cine = false;
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || !isplayer( p ) )
			continue;
		p cine_end();
		darkness_off( p );
		p.tod_house_hp0 = undefined;
	}
	if ( isdefined( level.tod_house_roll_trig ) )
		level.tod_house_roll_trig Delete();
	level.tod_house_roll_trig = undefined;
	if ( isdefined( level.tod_house_dome ) || isdefined( level.tod_house_fx ) )
		level thread dome_break();
	tod_shop::house_shop_end();
	level thread mood_off_later( 3.0 );   // the lights go out behind the party (the arena's own ride home takes ~1 s)
	dev_log( "END" );
}

function mood_off_later( secs )
{
	level endon( "end_game" );
	wait secs;
	mood_off();
}

// a looping effect on a tag_origin carrier at org (deleted by its owner)
function fx_host( effect, org )
{
	host = Spawn( "script_model", org );
	if ( !isdefined( host ) )
	{
		dev_log( "FX_DROPPED effect=" + effect + " (entity pool full)" );
		return undefined;
	}
	host SetModel( "tag_origin" );
	host.angles = ( 0, 0, 0 );
	host thread fx_host_play( effect );
	return host;
}

function fx_host_play( effect )   // self = the carrier
{
	self endon( "death" );
	wait 0.05;   // a snapshot: the client resolves tag_origin on the entity first
	PlayFXOnTag( effect, self, "tag_origin" );
}

// a one-shot effect at org on a carrier that deletes itself after `life` seconds
function fx_at( effect, org, life )
{
	host = fx_host( effect, org );
	if ( isdefined( host ) )
		host thread delete_after( life );
}

function delete_after( secs )   // self = an entity
{
	wait secs;
	if ( isdefined( self ) )
		self Delete();
}
