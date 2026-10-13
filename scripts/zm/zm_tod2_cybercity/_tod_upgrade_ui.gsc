// =============================================================================
// _tod_upgrade_ui.gsc — upgrade-choice UI, server half (logic + input).
//
// v2 = real LUI (ui/uieditor/menus/hud/tod_upgrade.lua, the map 1 4-file
// contract: this #precache + OpenLUIMenu, the CSC LuiLoad, the zone rawfile
// line). This module owns STATE + INPUT; the Lua is a dumb renderer fed by
// all-INT clientuimodel clientfields (18 as of v4.4, registered here + in
// the .csc twin in EXACT lockstep — a width/order mismatch corrupts the bit
// layout; APPEND ONLY). This module is the ONE home for every clientuimodel
// registration (upgrade panel + damage numbers + mag chip + class draft).
//
// Input (v4.4): a card is ALWAYS focused — D-PAD/stick switches, HOLD JUMP
// 0.5s locks (with a hold-progress bar via todUpgHold), release cancels.
// Focus pulse is SERVER-driven (this loop toggles bright/dim ~7 Hz — client
// UITimers are the map 1 leak trap). Sounds: tick on switch, confirm on
// lock, SUPER/ULTIMATE stings on reveal (aliases in sound/aliases/tod_ui.csv).
//
// tod_upgrades calls `player present_choice( opts, timeout )` -> returns 1|2.
// =============================================================================

#using scripts\shared\callbacks_shared;   // on_connect -> the per-life overlay rebuild
#using scripts\shared\clientfield_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\system_shared;
#using scripts\shared\util_shared;

#insert scripts\shared\shared.gsh;
#insert scripts\shared\version.gsh;

#precache( "lui_menu", "tod_upgrade" );
// v16.3 — the device latch's client notify (see pad_latch). Same precache trap
// as tod_upg_sync in _tod_upgrades.gsc: an unprecached eventstring never fires
// and nothing reports it.
#precache( "eventstring", "tod_input_pad" );
// RT 2026-10-05: THE TOAST's event (team_toast / self_toast below). Same precache trap: without this line the
// toast silently never fires.
#precache( "eventstring", "tod_toast" );

// Hold-to-lock duration. -35% (user 2026-08-21): 0.5 -> 0.325s.
#define TOD_UPG_HOLD_SECS   0.325
#define TOD_UPG_BLINK_SECS  0.15
// Damage-number accumulation window — one server frame. See push_dmg_num.
#define TOD_DMGNUM_WINDOW   0.05

// ---------------------------------------------------------------------------
// THE CARD REVEAL (v14.52) was REPLACED by THE PULL on 2026-09-28 (docs/187); its
// timings live with reveal_deal below (TOD_PULL_*).

// ---------------------------------------------------------------------------
// THE ULTIMATE AURA (v14.55, user 2026-08-31: "when you have an ultimate card
// displayed you will hear the aura sound that the heavenly altar makes. But
// this time its 2d and only your player hears it. Which makes sense since its
// your cards" + "make the aura sound like its coming from left or right
// depending on which side the ultimate is on ... if both cards are ultimate it
// sounds louder like an epic decision must be made").
//
// SAME LANE AS THE OVERCHARGE ZAP — `self PlayLocalSound()` on a repeating
// driver, which the user correctly pointed out was already proven
// (_tod_luck::overcharge_driver, v14.9b). PlayLocalSound is 2d and reaches ONE
// player; PlayLoopSound on an entity would broadcast to the whole lobby, so
// the retrigger is not a workaround, it IS the per-player mechanism here.
//
// PANNING IS BAKED INTO THE WAVS, not derived at runtime. The three units are
// pre-panned stereo cuts of tod_altar_aura.wav and the aliases are 2d, so the
// image is pinned to the SCREEN. A 3d emitter would have re-derived direction
// from world position and swung the aura around as the player turned their
// view — wrong for "the card on the left", and the panel does not lock the
// camera.
//
// UNIT 2.0s with 0.2s fades at both ends; retriggered every 1.8s so each pass
// crossfades over the seam. THAT 0.2s OVERLAP IS THE WHOLE TRICK — change one
// of these two and change the other. The tail after a pick is bounded by the
// unit length, and the 0.7s confirm flash covers most of it.
#define TOD_AURA_UNIT_SECS      1.8
// Hard ceiling on the driver, belt-and-braces beside its endons: it can never
// outlive the panel even if a future abort path forgets to notify. Sized off
// the choice window with room for the reveal.
#define TOD_AURA_MAX_PASSES     14
// A CO-OP STATION IS NOT A PAUSED WORLD. Round events run under
// level.tod_upgrade_pause, where the reveal is free; the personal upgrade
// station in CO-OP (the deliberate risk — see _tod_upgrades solo_present_run)
// leaves zombies live, so every tenth of a second of un-pickable card is real
// danger. Same show, run at this fraction of the clock.
// A SOLO STATION PICK NO LONGER TAKES THIS CUT (v16.84): it sets
// level.tod_upgrade_pause itself, so the test below already answers "paused"
// and the reveal plays at full speed. Nothing here changed — the flag became
// true in one more situation, and that is the situation this scale existed to
// avoid.
#define TOD_REVEAL_LIVE_SCALE   0.5

#namespace tod_upgrade_ui;

REGISTER_SYSTEM( "tod_upgrade_ui", &__init__, undefined )

function __init__()
{
	// MUST match _tod_upgrade_ui.csc EXACTLY (scope/name/version/bits/type,
	// same order). Our clientuimodel pool is otherwise empty.
	// CLASS TIERS widening (2026-08-22, docs/25 §8 Phase 0): the domain-id
	// fields grow 5 -> 6 bits (ids 1..63; the tier card is 24 and the per-gun
	// uniques 25..31 did not fit in 31). Paid for by todMagBonus 7 -> 1 — the
	// virtual mag pool was deleted 2026-08-20 and the field has read 0 ever
	// since. Net 61 -> 57 custom bits. ORDER UNCHANGED.
	clientfield::register( "clientuimodel", "todUpgShow",  VERSION_SHIP, 2, "int" );
	clientfield::register( "clientuimodel", "todUpgAD",    VERSION_SHIP, 6, "int" );   // 6 bits: domain ids 1..63 (was 5, 2026-08-22)
	clientfield::register( "clientuimodel", "todUpgAR",    VERSION_SHIP, 2, "int" );
	clientfield::register( "clientuimodel", "todUpgAL",    VERSION_SHIP, 4, "int" );
	clientfield::register( "clientuimodel", "todUpgBD",    VERSION_SHIP, 6, "int" );   // 6 bits: domain ids 1..63 (was 5, 2026-08-22)
	clientfield::register( "clientuimodel", "todUpgBR",    VERSION_SHIP, 2, "int" );
	clientfield::register( "clientuimodel", "todUpgBL",    VERSION_SHIP, 4, "int" );
	clientfield::register( "clientuimodel", "todUpgLuck",  VERSION_SHIP, 4, "int" );
	clientfield::register( "clientuimodel", "todUpgFocus", VERSION_SHIP, 3, "int" );
	clientfield::register( "clientuimodel", "todUpgTime",  VERSION_SHIP, 4, "int" );   // seconds left, 15..0
	// 2026-09-28 (docs/187): the dead todMagBonus bit RENAMED and reused - 1 = this deal has ONE card.
	// It replaces "BR == 0 means no second card", because the rarity fields now carry 0..3
	// (COMMON..LEGENDARY) and 0 is a real rarity. Same slot, same width, zero new bits.
	clientfield::register( "clientuimodel", "todUpgSolo",  VERSION_SHIP, 1, "int" );
	// Crosshair damage number: min(dmg,2047)*8 + reduced*4 + headshot*2 +
	// parity (parity flips per push so identical numbers re-pop). WIDENED
	// 13 -> 14 BITS (v13.9, user: sprinter hits "should be red ... to show you
	// are doing reduced damage") — the reduced bit rides the same field.
	// BUDGET: 58 -> 59 of the 61 PROVEN-BOOTED bits. Two left. Matching 14 in
	// the .csc register — the pair MUST move together (clientfield lockstep).
	clientfield::register( "clientuimodel", "todDmgNum",  VERSION_SHIP, 15, "int" );   // 14 -> 15 on 2026-09-09: the SCALE bit (hundreds / thousands). The pool is now 61 of 61.
	// Hold-to-lock progress 0..15 (the fill bar — SHARED by the upgrade panel
	// and the class draft; the two are never on screen together).
	clientfield::register( "clientuimodel", "todUpgHold", VERSION_SHIP, 4, "int" );
	// Class draft (_tod_class_select.gsc drives; tod_class_select.lua
	// renders): ONLY Show is class-specific — focus/time/hold RIDE the
	// todUpgFocus/todUpgTime/todUpgHold fields above (time is HALVED
	// server-side: 30s -> 15, the Lua displays x2). Show: 0 off / 1 choosing
	// / 2 locked-flash (the picked class = todUpgFocus at that moment).
	//
	// BUDGET (hard lesson 2026-08-19): the clientuimodel pool is SHARED with
	// stock zmhud.* + the Aetherium kit. 83 custom bits OVERFLOWED the pool
	// (Com_ERROR "clientuimodel is out of space" evicting zmhud.swordState =
	// map load aborts to the lobby). 61 custom bits was the last
	// PROVEN-BOOTED budget; this layout = 57 (the 2026-08-22 widening above
	// trimmed 4). Adding ANY field needs an equal trim.
	clientfield::register( "clientuimodel", "todClsShow",  VERSION_SHIP, 2, "int" );
	// (todFinaleWarn, THE FINALE ROAD BANNER's 1 bit, RETIRED 2026-10-05 with the
	// Map One ending, in BOTH VMs the same build: 61 -> 60 of the 61 proven bits.
	// One bit free; the next field still has to be weighed against the pool.)
	// RAMPAGE INDUCER (v14.20): 1 = hard mode is ON, and the Lua draws the RED
	// luck bar set instead of the amber one (tod_upgrade.lua LuckBar). APPENDED,
	// never inserted — the register ORDER is the wire format, so a field added
	// anywhere but the end re-numbers every field after it.
	//
	// WHY A NEW FIELD AND NOT A todUpgLuck WIDENING: todUpgLuck is 4 bits and
	// every value is spoken for — 0..10 are the eleven baked fill states and
	// 11..14 are v14.9's overcharge zap frames, leaving exactly ONE spare. The
	// red set needs fifteen more states, so it cannot ride that field, and
	// widening 4 -> 5 would not be an append.
	//
	// BUDGET (counted from the tree 2026-08-30, both VMs): the fifteen fields
	// above total 59 bits — 2+6+2+4+6+2+4+4+3+4+1+14+4+2+1. This one takes it
	// to 16 fields / 60 bits against the PROVEN ceiling of 18 / 61. One bit
	// left after this; the next feature needs the LuiNotifyEvent lane instead.
	//
	// NOT REUSING todMagBonus: it is a dead 1-bit field that has read 0 since
	// the mag pool was deleted, so it is tempting — but the name would then lie
	// about its contents, which is how the next reader gets misled.
	clientfield::register( "clientuimodel", "todRampage",  VERSION_SHIP, 1, "int" );
	// v17.93 FULL STEAM's wind goes PLAYER-ONLY (user 2026-09-05: "Other players
	// shouldnt be able to hear it"). It was a server PlayLoopSound on the player
	// entity with a 2D alias — every client rendered it at full volume. A
	// toplayer bit (its own pool, not the 61-bit clientuimodel budget) tells the
	// owner's client VM to run the loop locally; the .csc twin owns the handle.
	// LOCKSTEP with _tod_upgrade_ui.csc; the alias itself is TOD_LMGS_SFX in
	// _tod_upgrades.gsc and the literal in the .csc callback.

	// Guarantees every panel is down when the run ends — see clear_ui_on_end.
	level thread clear_ui_on_end();

	// The per-life overlay rebuild — see player_lui_life for the why.
	callback::on_connect( &on_player_connect );
}

// SHOTGUNS READ ONE PELLET (user 2026-08-25: "when i use a shot gun the damage
// indicators dont add up ... Im shooting the executioner and it shows 150 to the
// head but its killing the zombie on round 10").
//
// THE CAUSE IS THE CHANNEL, NOT THE MATH. todDmgNum is ONE clientuimodel field,
// and a networked field carries only its LAST value per server snapshot. A
// pellet shotgun raises one damage event PER PELLET, all inside the same server
// frame, so the eight writes below collapsed into one and the player saw a
// single pellet. The Executioner is 50/pellet x 8; a headshot is x3 = 150 per
// pellet — exactly the number reported — while the zombie actually ate 1,200.
// Nothing was wrong with the damage; only with what got drawn.
//
// MAP 1 HIT THIS AND SOLVED IT DIFFERENTLY: _acc_dev.gsc queues every event in a
// ring buffer and drains ONE per ~0.025s, so a shotgun reads as a fast flurry of
// eight separate numbers. That works, and it is why that map needed a parity bit
// and a self-terminating push loop. WE SUM INSTEAD, because the user asked for
// "a single damage number" and because summing is strictly cheaper: one network
// write per shot instead of eight, no drain loop to stall, and no queue to
// overflow on a Death Machine.
//
// THE WINDOW IS ONE SERVER FRAME. Pellets from one trigger pull all land in the
// same frame, so 0.05s captures a shot completely while staying at or below the
// fastest fireTime in the roster (Death Machine 0.05, PaP MP7 0.0512) — and on
// those two, merging two consecutive bullets into one number is a readability
// win rather than a loss. The window is FIXED, not extended per hit, so
// sustained fire can never accumulate without ever flushing.
//
// It also merges one shot across MULTIPLE zombies (a penetrating round, a pellet
// spread over a crowd). That is deliberate: the number answers "what did that
// shot do", which is the question being asked.
// PUBLIC — accumulate a crosshair damage number. self = the attacking player.
// The actual push happens in dmg_num_flush one frame later.
function push_dmg_num( dmg, headshot, reduced )
{
	if ( !isdefined( dmg ) || dmg <= 0 )
		return;
	if ( !isdefined( self.tod_dmg_acc ) )
		self.tod_dmg_acc = 0;
	self.tod_dmg_acc += dmg;
	if ( IS_TRUE( headshot ) )
		self.tod_dmg_acc_head = true;   // any pellet in the head colours the number
	if ( IS_TRUE( reduced ) )
		self.tod_dmg_acc_red = true;    // any armored (sprinter) hit REDDENS it —
		                                // same any-pellet rule as the headshot bit;
		                                // red WINS over headshot in the Lua, because
		                                // "you are doing reduced damage" is the fact
		                                // the user asked the colour to carry
	if ( !IS_TRUE( self.tod_dmg_acc_on ) )
	{
		self.tod_dmg_acc_on = true;
		self thread dmg_num_flush();
	}
}

// self = the attacking player. Threaded, because push_dmg_num is called from
// inside damage callbacks and a callback must never wait.
function dmg_num_flush()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	wait TOD_DMGNUM_WINDOW;

	total = self.tod_dmg_acc;
	head  = IS_TRUE( self.tod_dmg_acc_head );
	red   = IS_TRUE( self.tod_dmg_acc_red );
	self.tod_dmg_acc = 0;
	self.tod_dmg_acc_head = false;
	self.tod_dmg_acc_red = false;
	self.tod_dmg_acc_on = false;

	if ( isdefined( total ) && total > 0 )
		self push_dmg_num_now( total, head, red );
}

// HUNDREDS ENCODING (v17.64, 2026-09-05 — user: "we all saw 20470 cap
// damage"; the TENS cap of 2026-08-20 was the third time this ceiling was
// read as a bug, and shot-summing made it easy to reach): the 11-bit value
// carries dmg/100, the Lua displays x100. Cap = 204,700 shown, rounded to
// the nearest 100. Hits under 50 round to 0 and are floored to 100 — nothing
// in this roster does under 50 per shot at any tier, so no number goes blank.
// History: raw cap 2047 -> tens 20,470 (2026-08-20) -> hundreds 204,700.
// SUMMING MAKES THAT CAP EASIER TO REACH — a PaP shotgun headshot is now one
// number rather than eight. The field was widened 13 -> 14 bits in v13.9 to
// carry the REDUCED (red) bit: v = dmg*8 + reduced*4 + headshot*2 + parity,
// max 2047*8+7 = 16383 = 14 bits exactly. The dmg cap itself is unchanged.
// The Lua decode (tod_upgrade.lua todDmgNum subscription) moves in LOCKSTEP —
// /8 for the value, bit2 for red, bit1 for headshot; change one, change both.
// SEVEN DIGITS (2026-09-09, user: "Can we make the damage display numbers 7
// digits? We are easily passing 204700"). The field grew 14 -> 15 bits -- the
// LAST spare bit in the clientuimodel pool -- and the new bit is a SCALE:
// 0 = the value is hundreds (cap 204,700, as before), 1 = the value is
// THOUSANDS (204,800 .. 2,047,000 shown, rounded to the nearest 1,000). So
// v = dmg*16 + scale*8 + reduced*4 + headshot*2 + parity, max 32767 = 15 bits.
// The Lua decode (tod_upgrade.lua todDmgNum subscription) moves in LOCKSTEP.
// POWER SCALE (2026-09-25, user: "so players can easily identify how much damage
// they do"). Every hit is a tenth of what it was, so the number is now EXACT:
// scale 0 = the value IS the damage (1 .. 2,047, every single hit in the roster),
// scale 1 = hundreds (2,100 .. 204,700 for big summed crowd hits) - the same
// ceiling the thousands scale gave before, in the new units. Same 15 bits; the
// Lua decode (tod_upgrade.lua todDmgNum) moves in LOCKSTEP: scale 0 -> x1, 1 -> x100.
function push_dmg_num_now( dmg, headshot, reduced )
{
	scale = 0;
	dmg = int( dmg + 0.5 );
	if ( dmg > 2047 )
	{
		scale = 1;
		dmg = int( ( dmg + 50 ) / 100 );
	}
	if ( dmg > 2047 )
		dmg = 2047;
	if ( dmg < 1 )
		dmg = 1;
	if ( !isdefined( self.tod_dmg_parity ) )
		self.tod_dmg_parity = 0;
	self.tod_dmg_parity = 1 - self.tod_dmg_parity;
	v = dmg * 16 + scale * 8 + self.tod_dmg_parity;
	if ( IS_TRUE( headshot ) )
		v += 2;
	if ( IS_TRUE( reduced ) )
		v += 4;
	self clientfield::set_player_uimodel( "todDmgNum", v );
}

// EVERY PANEL CLEARS ON end_game (audit 2026-08-25). todUpgShow is only zeroed
// on the NORMAL exit of a card pick, and the HEAVENLY GIFT ALTAR deliberately
// does NOT pause the world — so a wipe while a card was up left the panel
// frozen over the game-over screen. One thread with NO endon, so
// it is guaranteed to run on every exit path including ones added later.
function clear_ui_on_end()
{
	level waittill( "end_game" );
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) )
			continue;
		p set_field( "todUpgShow", 0 );
		p set_field( "todClsShow", 0 );
		p set_field( "todUpgHold", 0 );
	}
}

// PUBLIC — RAMPAGE INDUCER (v14.20). self = player. Flips that player's luck
// bar between the amber set and the red/purple one. _tod_rampage.gsc is the
// only caller and the only writer of level.tod_rampage_on.
//
// PUSHED ON EVERY SPAWN, not just on toggle: the engine closes a player's LUI
// menus on death -> spectate and the HUD is rebuilt per life, so a
// toggle-only push would leave a revived player looking at an amber bar in a
// rampaged match. Same per-life re-assert discipline the rest of this file
// uses (aetherium-and-upgrade-input memory).
function set_rampage( on )
{
	v = 0;
	if ( IS_TRUE( on ) )
		v = 1;
	self clientfield::set_player_uimodel( "todRampage", v );
}

// self = player. Open the always-on overlay once (additive — cannot break the
// stock HUD; the widget stays invisible until todUpgShow goes nonzero).
function ensure_menu()
{
	if ( !isdefined( self.tod_upg_menu ) )
		self.tod_upg_menu = self OpenLUIMenu( "tod_upgrade" );
}

// ---------------------------------------------------------------------------
// PER-LIFE OVERLAY REBUILD (live report 2026-08-26: "when you get finished and
// you spectate your team and respawn half of the UI go away ... you can't
// choose the upgrade ... can't see the luck ... can't see where are you in
// the map").
//
// THE ENGINE CLOSES A PLAYER'S OpenLUIMenu MENUS ON THE DEATH -> SPECTATE
// TRANSITION, and ensure_menu()'s handle guard reads self.tod_upg_menu — a
// SERVER-side field that transition never clears — so after a respawn the
// guard was permanently satisfied and the menu never reopened. The player
// lost the entire tod_upgrade overlay for the rest of the match: upgrade
// cards, luck bar, tower gauge, damage numbers, finale banner — exactly the
// list in the report. (The upgrade EVENTS still ran server-side; the player
// was choosing blind.)
//
// This is map 1's fix ported (_acc_lui::player_lui_init; its user report
// 2026-06-24 was the same bug: "drops + perks don't show after a player dies
// and respawns"): reopen once per LIFE, then re-arm every change-gated feed
// so it re-pushes CURRENT state into the just-opened menu. Map 1 proved both
// halves: a value that hasn't changed since its last push never repaints a
// fresh menu on its own, and a same-value set_player_uimodel re-set DOES
// repaint once the GSC-side change tracker is cleared. "spawned_player"
// fires on the initial spawn AND every co-op respawn (stock _zm.gsc notify),
// so one loop covers both.
//
// The Aetherium kit needs none of this: it replaces T7Hud_zm_factory, the
// stock HUD menu, whose lifecycle the engine itself re-runs per spawn. The
// class-draft menu (tod_class_select) is round-1-once in a paused world and
// is never needed again, so it is deliberately not rebuilt here.
// ---------------------------------------------------------------------------
function on_player_connect()
{
	self thread player_lui_life();
}

function player_lui_life()
{
	self endon( "disconnect" );
	level flag::wait_till( "initial_blackscreen_passed" );

	b_first = true;
	for ( ;; )
	{
		// Respawns need a beat for the fresh client HUD to settle before the
		// reopen lands (map 1's 0.5s). Match start opens near-instantly so
		// the overlay is up the moment the fade lifts.
		if ( b_first )
			wait 0.05;
		else
			wait 0.5;
		b_first = false;

		if ( isdefined( self.tod_upg_menu ) )
			self CloseLUIMenu( self.tod_upg_menu );
		self.tod_upg_menu = undefined;
		self ensure_menu();
		wait 0.1;   // let the menu instantiate client-side before data lands

		// v16.3 — re-tell the fresh HUD Lua which device this player has proved
		// (pad_latch). CoD.TodPad is a client-VM global and normally survives
		// the rebuild; the resend is one int and closes the case where the
		// first d-pad press beat the first menu.
		if ( IS_TRUE( self.tod_input_pad ) )
			self LuiNotifyEvent( &"tod_input_pad", 1, 1 );

		// Re-arm the change-gated feeds so each re-pushes into the new menu:
		// the tower gauge + boss pip + max-HP lanes (_tod_gauge's 0.35s loop
		// re-sends the moment its per-player trackers read undefined) ...
		self.tod_gauge_f = undefined;
		self.tod_gauge_bf = undefined;
		self.tod_gauge_mh = undefined;
		// ... including the v14.50 DOWNED-TEAMMATE cells, which need this more
		// than any other feed on the list: a player who just bled out and
		// respawned is precisely the one whose teammates are likely to be down
		// RIGHT NOW, and that mask only pushes when it CHANGES. Without these
		// two the fresh HUD would show no red until somebody else went down or
		// got picked up — a marker missing at the exact moment it matters.
		self.tod_gauge_dlo = undefined;
		self.tod_gauge_dhi = undefined;
		// ... and the ROUND READOUT (v17.25). THIS ONE IS NOT FOR THIS MENU.
		// tod_round is drawn by AetheriumRoundCounter, which lives in the KIT
		// HUD — the menu the header above says needs none of this, because the
		// engine re-runs its lifecycle per spawn. That is exactly the problem:
		// the engine rebuilds the widget, and a change-gated feed then says
		// nothing to it until the round flips, which can be minutes. A fresh
		// counter reading ROUND 1 in round 40 is the failure. The re-arm rides
		// here because "spawned_player" is already what this loop waits on, and
		// _tod_gauge re-sends within one 0.35s tick of the tracker going
		// undefined.
		self.tod_round_shown = undefined;
		// ... and the PACK-A-PUNCH TIER BADGE (v17.33), for the same reason and
		// with the same owner. It lives in AetheriumLoadout — the KIT HUD,
		// rebuilt by the engine on every spawn — and its feed only pushes on
		// change, so without this a respawning player's badge would read
		// UNPACKED until they next switched weapons or bought a tier. A player
		// who just bled out holding a packed gun is precisely who notices.
		self.tod_pap_tier_shown = undefined;
		// ... and the luck bar, whose pushes only ride luck CHANGES —
		// re-assert the current value directly. The upgrade cards need
		// nothing (every event re-sets its fields from scratch, todUpgShow
		// 0->1 included) and the finale banner's blink re-pushes all players
		// every cycle, so both self-heal.
		pct = 0;
		if ( isdefined( self.tod_luck_bar ) )
			pct = self.tod_luck_bar;
		self set_luck_pct( pct );

		self waittill( "spawned_player" );   // next death -> respawn: rebuild
	}
}

// domain key -> the Lua DOMAIN table id (MUST mirror tod_upgrade.lua AND the
// register_domains order in _tod_upgrades.gsc). v4 matrix 2026-08-19.
function domain_id( key )
{
	switch ( key )
	{
		case "damage":     return 1;
		case "dr":         return 2;    // DMG REDUCTION — v16: DIMINISHING ladder 6/11/15/18/20% cumulative (was flat 5%/Lv to 25%) and S -> A band. The two boss lanes CALL tod_upgrades::dr_mult() now; they used to carry hand-copied literals
		case "bounty":     return 3;
		case "luck":       return 4;
		case "sprint":     return 29;   // SPRINT — CLASS PASS 2 (2026-09-27): the ARCHER's, 9 levels, faster SPRINTING only; moved 5 -> 29 (5 is REAPER'S REACH since 2026-09-27; 29 freed by AERIALIST). History: v16: A -> S band (user: "sprint needs to be moved to S tier"), so weight 50 -> 20 and the SUPER/ULTIMATE slice x0.75 -> x0.50. Ladder unchanged (speed_pct_for_level)
		case "deadeye":    return 6;    // DEADEYE (2026-09-27) - the Archer's CORE WEAPON card; reuses retired HEADSHOT's id (no plate zoned; text row)
		case "headshot":   return 6;    // retired
		case "heavyhands": return 7;    // HEAVY HANDS (2026-09-27) - the Warrior's CORE WEAPON card; reuses retired MAG SIZE's id (no plate zoned; text row)
		case "magsize":    return 7;    // MAG SIZE — 2026-09-02: A -> S band (user: "We need to move mag size upgrade to s tier"), so weight 50 -> 20 and the SUPER/ULTIMATE slice x0.75 -> x0.50. Ladder untouched (MAG_STEP), so the card art stands
		case "reserve":    return 8;
		case "mobility":   return 9;
		case "bulletfeed": return 10;
		case "echo":       return 11;
		case "regen":      return 12;
		case "leech":      return 13;
		case "cleave":     return 14;
		case "firerate":   return 15;
		case "handling":   return 16;
		case "recoil":     return 17;
		case "knifespeed": return 18;
		case "penetration": return 19;
		case "thunder":     return 20;
		case "sprintfire":  return 21;
		case "lunge":       return 22;   // CHAIN LUNGE (2026-08-22)
		case "runandgun":   return 23;   // RUN AND GUN (2026-08-22) — skirmisher ammo saver
		// CLASS TIERS (docs/25, 2026-08-22). The field is 6 bits now (1..63).
		case "tier":        return 24;   // the TIER card — AL/BL carry (class-1)*2 + (tier-2)
		case "adrenaline":  return 25;   // MP5  (skirmisher T2) — kills grant a speed burst
		case "overdrive":   return 26;   // Death Machine (heavy T3, moved off the MP7 2026-08-23)
		case "killreload":  return 27;   // KILL RELOAD — REMOVED 2026-09-01 (user: "No one likes it"); id stays mapped, same form as 28 below
		case "impact":      return 28;   // ASSAULT, any gun (un-bound from the AK-47 2026-08-23)
		case "suppress":    return 29;   // HK21 (heavy T2)      — hits slow the horde
		case "grinder":     return 30;   // Death Machine (heavy T3) — keep firing, hit harder
		case "meleerange":  return 31;   // MELEE RANGE (2026-09-26, the Warrior) reuses DRAW CUT's id (docs/upgrade_ids.md); the drawcut line below is history
		case "drawcut":     return 31;   // the Warrior's T2 blade (Gauntlet of Siegfried since 2026-09-26) — swings out of a sprint hit harder
		case "sprintarmor": return 32;   // SPRINT ARMOR (2026-08-23) — skirmisher-only since v14.11 (slasher dropped), -5%/Lv damage while sprinting
		case "secondwind":  return 33;   // SECOND WIND (2026-08-23) — skirmisher, MP5-bound since v14.11 (was MP7), sprint to heal 1%/Lv per second
		case "momentum":    return 34;   // MOMENTUM — REMOVED v14.11 (2026-08-30); stays mapped, see the note below
		case "bossdmg":     return 35;   // GIANT SLAYER (2026-08-23, v9.45) — assault, +15%/Lv vs the boss/elite triad (3->4->5->8->15 in nine days; 15 since v15, 2026-08-31)
		case "backarmor":   return 36;   // BACK ARMOR (2026-08-23, v9.45) — heavy-only since v14.11 (assault dropped); v16 max 3 -> 5 on the shared ladder5(), -10/18/24/28/32% from a rear arc
		case "march":       return 37;   // FORCED MARCH (2026-08-24) — assault, AK-47-bound, +5% move speed/Lv (card art + pause plate r37 landed 2026-08-24)
		case "vitality":    return 37;   // VITALITY — CLASS PASS 2 (2026-09-27): the WARRIOR's, 6 levels, flat +10 HP / Lv (TOD_VITALITY_HP_LV); moved 38 -> 37 (38 is SUMMONING POWER since 2026-09-26; 37 freed by DEMOLITIONIST). History: VITALITY (v14.11) — heavy, scope class; v16 put it on ladder5() as FLAT HP: +10/18/24/28/32 (TOD_UPG_VITALITY_HP_PER_LVL is DEAD). Card art + pause plate r38 landed 2026-08-30
		case "recovery":    return 39;   // RECOVERY (v14.11) — heavy; v16 max 3 -> 5 on ladder5(), regen starts 10/18/24/28/32% sooner. Card art + pause plate r39 landed 2026-08-30
		case "perkslots":   return 40;   // PERK SLOTS — REMOVED 2026-09-03 (v16.80, user: "remove the perk limit"); id stays mapped, same form as 27 above
		case "distraction": return 41;   // DISTRACTION (v14.59; reshaped v16.49) - assault Cymbal Monkey; the level IS the carry cap (1/2/3), Max Ammo +1. Weapon lane in _tod_distraction.gsc; scope class, max 3. Art + pause plate r41 landed 2026-09-01; cards re-baked for 3 pips (docs/75)
		case "gunslinger":  return 44;   // GUNSLINGER (v16.51) — slasher; class secondary vs bosses/elites x(1 + 0.30/Lv) on top of the 2.25x class baseline, in slasher_sidearm_boss_mult. Scope class, max 5, band B. Art + pause plate r44 PENDING (docs/79): text fallbacks until then
		case "trailblazer": return 46;   // TRAILBLAZER (v16.62) — skirmisher; burning ground trail while sprinting: longer, wider, hotter per Lv (docs/80). Scope class, max 5, band A. Art PENDING (docs/83): text fallbacks
		case "athlete":     return 43;   // ATHLETE (v16) — slasher; +10% slide speed, +25% jump height and (v16.23-28) strafe-axis air steering at 120 + 60/Lv deg/s, momentum free in the front hemisphere, 35% at a reversal. Mechanic in _tod_athlete.gsc (per-player SetVelocity, never the GLOBAL SetJumpHeight). Art + pause plate r43 landed 2026-09-01
		case "riotshield":  return 45;   // RIOT SHIELD (v16.63, 2026-09-02) — UNIVERSAL; a shield that recharges after it breaks, 200..500 HP and 4:00..2:00 per level. Weapon lane in _tod_riotshield.gsc; scope class, max 5, band A. Art + pause plate r45 PENDING (docs/82): text fallbacks until then
		case "deadshot":    return 47;   // DEADSHOT (v16.64, 2026-09-02) — assault; perma head-snap aim assist (the engine's Deadshot, UseAlternateAimParams), shows in the perk bar, no perk slot. Max 1, band S, ALWAYS dealt as ULTIMATE (set_rarity_lock). Effect lane _tod_deadshot.gsc|.csc. ONE card only (docs/84) PENDING: text fallback; no pause plate requested (text row)
		case "lmgsprint":   return 42;   // FULL STEAM (v15) — heavy; sprint 0.8s unbroken for the speed ladder (TOD_LMGS_ARM_MS, 1500 -> 1000 -> 800 in v16). Replaced MOBILITY (id 9, retired same commit). Card art + pause plate r42 landed 2026-09-01; the three cards were re-baked the same day to the NUMBERLESS "KEEP SPRINTING FOR SPEED", so an arm-time retune no longer owes an art pass (docs/56 amendment, closed)
		case "retriever":   return 57;   // HELL'S RETRIEVER (2026-09-26) - assault; the lethal is earned by this card. Max 8, band A, no dark. No CARD_SLUG and no pause plate yet: text fallback
		case "reaperreach":  return 5;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art)
		case "packmaster":   return 10;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art)
		case "soulsiphon":   return 17;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art)
		case "burnedout":    return 19;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art) - RETIRED 2026-09-27 class pass 2 (id 19 -> summonmaster)
		case "shotspeed":    return 35;   // SHOT SPEED (Archer, 6 levels) - 2026-09-27 class pass 4 (user); freed by SHADOWSTEP. Text card + text row
		case "pierce":       return 26;   // PIERCING (Archer, 9 levels) - 2026-09-27 CLASS PASS 3 (user); freed by HUNTER'S MARK. Text card + text row
		case "huntersmark":  return 26;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art)
		case "aerialist":    return 29;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art) - RETIRED 2026-09-27 class pass 2 (id 29 -> sprint)
		case "shadowstep":   return 35;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art)
		case "pointblank":   return 36;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art) - RETIRED 2026-09-27 class pass 2 (id 36 -> fusion)
		case "demolition":   return 37;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art) - RETIRED 2026-09-27 class pass 2 (id 37 -> vitality)
		case "bulwark":      return 42;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art)
		case "executioner":  return 12;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art) - RETIRED 2026-09-27 class pass 2 (id 12 -> demonslayer)
		case "sweep":        return 48;   // CLEAVE (Warrior, 9 levels) - 2026-09-27 class pass 4 (user); freed by BATTLE RHYTHM. Text card + text row
		case "rhythm":       return 48;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art) - RETIRED 2026-09-27 class pass 2 (id 48 free)
		case "juggernaut":   return 9;   // 2026-09-27 class build card (reuses a retired id; text card + text row until art) - RETIRED 2026-09-27 class pass 2 (id 9 -> cloak)
		// ---- CLASS PASS 2 (2026-09-27): the six new cards take the ids their retired
		// cards freed the same day (docs/upgrade_ids.md). The retired keys' lines stay as history.
		case "fusion":       return 36;   // EXPLOSIVE FUSION (Breacher, 9 levels since 2026-09-28) - freed by POINT BLANK. Text card + text row
		case "demonslayer":  return 12;   // DEMON SLAYER (Warrior, 9 levels) - freed by EXECUTIONER. Text card + text row
		case "summonmaster": return 19;   // SUMMONER MASTER (Necromancer, 9 levels) - freed by BURNED OUT. Text card + text row
		case "cloak":        return 9;    // INVISIBILITY CLOAK (Necromancer tactical, 9 levels) - freed by JUGGERNAUT. Text card + text row
		case "buckshot":    return 58;   // BUCKSHOT (2026-09-27) - the Breacher's CORE WEAPON card; takes PELLETS' id (PELLETS folded into it)
		case "pellets":     return 58;   // PELLETS (2026-09-26) - Breacher; twin axis "e", max 3, band A, no dark. No CARD_SLUG / plate: text fallback
		case "c4":          return 60;   // STICKY C4 (2026-09-26) - Breacher; the lethal is EARNED: charges 1..4 and x1.0..x2.4 damage over max 8, band A, no dark. Text fallback. (59 EXPLOSIVES was cut the same day - FREE)
		case "cluster":     return 61;   // CLUSTER (2026-09-26) - Breacher; the tactical is EARNED: charges 1..3 and x1.0..x2.4 damage over max 8, band A, no dark. Text fallback
		case "bash":        return 62;   // BASH (2026-09-26) - Warrior tactical, Hellbound's 8-level ladder (_tod_class_kit.gsc TOD_BASH_*), band A, no dark. Text fallback
		case "soulbomb":    return 59;   // SOUL BOMB (2026-09-26) - Necromancer lethal card, 8 levels (_tod_necro_summon TOD_BOMB_*), band A, no dark. Text fallback. 59 = the never-shipped EXPLOSIVES id
		case "summonpower": return 38;   // SUMMONING POWER (2026-09-26) - Necromancer helpers, 8 levels (TOD_POWER_*), band A, no dark. REUSES retired VITALITY's id (docs/upgrade_ids.md); text fallback + TodTextPlate
		case "soulbeam":    return 39;   // SOUL BEAM (2026-09-26) - Necromancer skull beam, 5 levels (TOD_BEAM_*), band A, no dark. REUSES retired RECOVERY's id; text fallback + TodTextPlate
		case "gravsmash":   return 63;   // GRAVITY SMASH (2026-09-26) - Warrior lethal, 8 levels (TOD_GS_*), band A, no dark. Text fallback. 63 IS THE LAST 6-BIT ID: reuse retired ids (docs/upgrade_ids.md)
		// NOTE "echo" (11), "regen" (12), "lunge" (22), "grinder" (30) and
		// "momentum" (34) are still mapped above even though all five domains
		// were removed (echo + grinder 2026-08-23, CHAIN LUNGE 2026-08-24,
		// regen + momentum v14.11 2026-08-30). This switch is a KEY->id map,
		// not an ordered list, so a stale case is inert and removing one would
		// only risk disturbing ids that the Lua and the pause plates depend on.
	}
	return 0;
}

function set_field( name, v )   // self = player
{
	self clientfield::set_player_uimodel( name, v );
}

// PUBLIC — live luck-bar push, 0..100 -> tens (self = player). The top-left
// luck bar is all-LUI now (tod_upgrade.lua swaps baked i_tod_luck_NN images
// on todUpgLuck);
// _tod_luck calls this on every bar change. present_choice re-sets the same
// field at event time for the card readout — same scale, no conflict.
function set_luck_pct( pct )
{
	v = int( pct / 10 );
	if ( v > 10 )
		v = 10;
	if ( v < 0 )
		v = 0;
	// The HUD menu hosts the luck bar — but never OpenLUIMenu pre-blackscreen
	// (the field set itself is safe anytime; the menu reads it on subscribe).
	if ( level flag::get( "initial_blackscreen_passed" ) )
		self ensure_menu();
	self set_field( "todUpgLuck", v );
}

// self = player. THE PULL (docs/187, user 2026-09-28): "there's a reason why
// players love crates in csgo. They always go through the animation but it's
// the anticipation." Every card is dealt FACE-DOWN and CLIMBS the rarity ladder
// one rung at a time - COMMON white, RARE blue, EPIC purple, LEGENDARY gold -
// until it stops, then flips. Auto, never skippable (user).
//
// THE SERVER OWNS EVERY BEAT, so the choreography scales with the live-world
// factor like everything else here, and the client has no clock to drift.
// Three field edges drive the Lua, never two in one snapshot (a real wait
// separates every push):
//   todUpgHold RISES      a BEAT on the active slot: the first beat of a slot
//                         starts its climb at rung 0, every later one is the
//                         heartbeat hitch at the end of a rung ("will it stop?").
//                         todUpgHold is 0 and unused while focus == 0, and the
//                         Lua ignores it falling, so present_choice's reset
//                         after the reveal is silent.
//   todUpg<slot>R changes the active card CLIMBS to that rung (wire 0..3).
//   todUpg<slot>D 0 -> N  the card FLIPS at its current rung.
// The active slot is derived client-side: A while AD == 0, then B while BD == 0.
//
// Runs INSIDE present_choice's thread (not threaded), so the caller's endons -
// "disconnect", "end_game", "tod_solo_down_abort" - kill it exactly like they
// kill the rest of the flow; the abort paths already clear todUpgShow.
//
// TIMINGS in seconds at a paused world (the prototype's, docs/187 section 4).
// A rung's dwell INCLUDES its hitch. LOCKSTEP with tod_upgrade.lua's PULL_*:
// a Lua tween that can be overtaken by the next push must finish inside the
// shortest push gap, the hitch (0.19 x TOD_REVEAL_LIVE_SCALE 0.5 = 95 ms). The
// flips run after their slot's LAST push and are bounded by the beat instead.
#define TOD_PULL_OPEN          0.38   // backs on the table before slot A's climb
#define TOD_PULL_HITCH         0.19   // the heartbeat at the end of every rung
#define TOD_PULL_RUNG_1        0.44   // COMMON   (dwell incl. hitch)
#define TOD_PULL_RUNG_2        0.48   // RARE
#define TOD_PULL_RUNG_3        0.58   // EPIC
#define TOD_PULL_RUNG_4        0.82   // LEGENDARY
#define TOD_PULL_BEAT_1        0.26   // after a COMMON flips, before the next slot
#define TOD_PULL_BEAT_2        0.40
#define TOD_PULL_BEAT_3        0.65
#define TOD_PULL_BEAT_4        1.00
#define TOD_PULL_TAIL          0.25   // last card flips -> input opens
// THE REACH (docs/201 section 4, user 2026-10-02: the near miss / almost hit). After a heartbeat a card can
// STRAIN for the next rung: it then comes SO CLOSE (falls back and flips where it was: a near miss, on its final
// rung) or BREAKS THROUGH (climbs on: a comeback, from the rung below a RARE+ card's final rung). Decided from the
// card's REAL result, which was rolled before the reveal began: the reach is theatre, never the odds. One reach
// per deal at most. THE WIRE (zero new bits): a REACH is a second todUpgHold beat at the same rung with no climb
// between; the NEXT edge resolves it - a climb = BREAK THROUGH, one more beat = SO CLOSE (then the flip). The
// worst-case deal goes from 10 beats to 11 of todUpgHold's 15. LOCKSTEP the two waits with TodPull.lua REACH_MS /
// REACH_SETTLE_MS, and the table below with docs/201 section 4.
#define TOD_PULL_REACH         0.62   // the strain toward the next rung (the swell holds the whole time)
#define TOD_PULL_REACH_SETTLE  0.26   // SO CLOSE: the sag, before the card's own sting
// the chance a card reaches, by its REAL rarity (1 COMMON .. 4 LEGENDARY), per hundred
#define TOD_PULL_NEAR_1        12     // SO CLOSE to RARE      (needs 2 levels of room)
#define TOD_PULL_NEAR_2        18     // SO CLOSE to EPIC      (needs 3)
#define TOD_PULL_NEAR_3        30     // SO CLOSE to LEGENDARY (needs 4)
#define TOD_PULL_BREAK_2       10     // BREAK THROUGH from COMMON to RARE
#define TOD_PULL_BREAK_3       25     // BREAK THROUGH from RARE to EPIC
#define TOD_PULL_BREAK_4       60     // BREAK THROUGH from EPIC to LEGENDARY
function reveal_deal( opts )
{
	sc = 1.0;
	if ( !IS_TRUE( level.tod_upgrade_pause ) )
		sc = TOD_REVEAL_LIVE_SCALE;

	// THE HEAVENLY AURA IS LEGENDARY'S ALONE now (docs/187) - decided from
	// reveal_rarity, so a floor-gated tier card never summons one.
	leg_a = ( reveal_rarity( opts[ 0 ] ) >= 4 );
	leg_b = ( isdefined( opts[ 1 ] ) && reveal_rarity( opts[ 1 ] ) >= 4 );

	// THE REACH: decided before the first back moves, from the results already rolled
	plan = self reach_plan( opts );

	self.tod_pull_beat = 0;
	wait( TOD_PULL_OPEN * sc );

	self reveal_slot( "A", opts[ 0 ], sc, plan );
	if ( leg_a && !leg_b )
		self thread ultimate_aura( "tod_upg_aura_l" );
	self wait_beat( reveal_rarity( opts[ 0 ] ), sc );

	if ( isdefined( opts[ 1 ] ) )
	{
		self reveal_slot( "B", opts[ 1 ], sc, plan );
		if ( leg_a && leg_b )
			self thread ultimate_aura( "tod_upg_aura_both" );
		else if ( leg_b )
			self thread ultimate_aura( "tod_upg_aura_r" );
		self wait_beat( reveal_rarity( opts[ 1 ] ), sc );
	}

	wait( TOD_PULL_TAIL * sc );
}

// self = player. The breath after a card flips - longer the rarer, so the flip
// has room to land before the next back starts climbing.
function wait_beat( rar, sc )
{
	t = TOD_PULL_BEAT_1;
	if ( rar == 2 )
		t = TOD_PULL_BEAT_2;
	else if ( rar == 3 )
		t = TOD_PULL_BEAT_3;
	else if ( rar >= 4 )
		t = TOD_PULL_BEAT_4;
	wait( t * sc );
}

// self = player. One tick of the beat counter (see the header above).
function pull_beat()
{
	self.tod_pull_beat++;
	if ( self.tod_pull_beat > 15 )
		self.tod_pull_beat = 15;   // 4 bits; a deal needs at most 2 x (1 + 4) = 10, +1 with THE REACH (docs/201) = 11
	self set_field( "todUpgHold", self.tod_pull_beat );
}

// THE AURA DRIVER - the heavenly altar's own pad, pre-panned to the side its
// card is on, retriggered per-player until the panel is done with it. Played
// for a LEGENDARY since 2026-09-28 (it was the ULTIMATE's). PlayLocalSound is 2d
// and reaches ONE player; a loop on an entity would broadcast to the lobby.
// Unit 2.0 s with 0.2 s fades, retriggered every 1.8 s (the overlap IS the
// crossfade). FOUR WAYS OUT: the panel is torn down on more paths than it is
// closed on, and the pass ceiling stops it even if every endon is missed.
function ultimate_aura( alias )
{
	self endon( "disconnect" );
	self endon( "tod_upg_aura_stop" );
	self endon( "tod_solo_down_abort" );
	level endon( "tod_global_upg_takeover" );
	level endon( "end_game" );

	for ( i = 0; i < TOD_AURA_MAX_PASSES; i++ )
	{
		self PlayLocalSound( alias );
		wait TOD_AURA_UNIT_SECS;
	}
}

// The rarity this option is REVEALED at, which is not always the rarity it was
// rolled at. A floor-gated CLASS TIER card cannot be taken - giving it the full
// climb and then refusing the pick is a tease, not a reward, so a locked slot
// always reveals as a plain COMMON: quick, quiet, no build-up.
function reveal_rarity( o )
{
	if ( IS_TRUE( o.locked ) )
		return 1;
	r = o.rarity;
	if ( !isdefined( r ) || r < 1 )
		r = 1;
	if ( r > 4 )
		r = 4;
	return r;
}

// THE REACH's plan for one deal (docs/201 section 4): undefined = no reach, else a struct { slot "A" / "B",
// rung = the rung the card strains FROM (1..3), win = true for a BREAK THROUGH to rung + 1, false for SO CLOSE
// (it stops at rung) }. The left card rolls first; the right one can only reach if the left did not. Rolled from
// results that already exist and never touches them.
function reach_plan( opts )
{
	if ( !isdefined( opts ) )
		return undefined;
	names = array( "A", "B" );
	for ( i = 0; i < 2; i++ )
	{
		o = opts[ i ];
		if ( !isdefined( o ) )
			continue;
		kind = reach_roll( o );
		if ( kind == 0 )
			continue;
		p = SpawnStruct();
		p.slot = names[ i ];
		p.win = ( kind == 2 );
		r = reveal_rarity( o );
		p.rung = r;
		result = "so_close";
		if ( p.win )
		{
			p.rung = r - 1;
			result = "break_through";
		}
		forced = 0;
		if ( isdefined( o.tod_reach_force ) )
			forced = o.tod_reach_force;
		self pull_log( "REACH slot=" + p.slot + " domain=" + o.domain + " rung=" + p.rung + " result=" + result + " rarity=" + r + " cur=" + o.cur + "/" + o.max + " forced=" + forced );
		return p;
	}
	return undefined;
}

// One card's reach, by its REAL result: 0 none, 1 SO CLOSE (at its final rung, only when the domain had room
// for the rung above: never tease what could not have happened), 2 BREAK THROUGH (RARE or better). Never on the
// CLASS TIER card, a floor-locked card or a rarity-locked domain. A dev CARD TEST card may force its reach
// (o.tod_reach_force 1 / 2), still only where it is possible.
function reach_roll( o )
{
	if ( IS_TRUE( o.locked ) || o.domain == "tier" || IS_TRUE( o.rarity_locked ) )
		return 0;
	r = reveal_rarity( o );
	near_ok = ( r <= 3 && isdefined( o.max ) && isdefined( o.cur ) && ( o.max - o.cur ) >= r + 1 );
	if ( isdefined( o.tod_reach_force ) )
	{
		if ( o.tod_reach_force == 1 && near_ok )
			return 1;
		if ( o.tod_reach_force == 2 && r >= 2 )
			return 2;
		return 0;
	}
	b = reach_break_pct( r );
	n = 0;
	if ( near_ok )
		n = reach_near_pct( r );
	x = RandomInt( 100 );
	if ( x < b )
		return 2;
	if ( x < b + n )
		return 1;
	return 0;
}

function reach_near_pct( r )
{
	if ( r == 1 )
		return TOD_PULL_NEAR_1;
	if ( r == 2 )
		return TOD_PULL_NEAR_2;
	if ( r == 3 )
		return TOD_PULL_NEAR_3;
	return 0;
}

function reach_break_pct( r )
{
	if ( r == 2 )
		return TOD_PULL_BREAK_2;
	if ( r == 3 )
		return TOD_PULL_BREAK_3;
	if ( r >= 4 )
		return TOD_PULL_BREAK_4;
	return 0;
}

// Dev-only console record of the reveal (the map's PrintLn pattern: the string is built outside the developer
// block, the call stays inside it). Logs [TOD_PULL] REACH and STREAK_REPORT.
function pull_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	n = -1;
	if ( isdefined( self ) && isplayer( self ) )
		n = self GetEntityNumber();
	line = "[TOD_PULL] ms=" + GetTime() + " player=" + n + " " + msg;
	/#
	PrintLn( line );
	#/
}

// self = player. One slot: climb rung by rung to its rarity, then flip. plan = reach_plan's (or undefined).
function reveal_slot( slot, o, sc, plan )
{
	rar = reveal_rarity( o );
	reach_at = 0;
	reach_win = false;
	if ( isdefined( plan ) && plan.slot == slot )
	{
		reach_at = plan.rung;
		reach_win = plan.win;
	}
	for ( k = 1; k <= rar; k++ )
	{
		// the climb: rung 1 is the slot's first beat, every later rung a rarity push
		if ( k == 1 )
			self pull_beat();
		else
			self set_field( "todUpg" + slot + "R", k - 1 );
		// a BREAK THROUGH's climb crashes through instead of the plain rung tone
		if ( reach_win && k == reach_at + 1 )
			self PlayLocalSound( "tod_pull_break" );
		else
			self PlayLocalSound( "tod_pull_rung_" + k );

		dwell = TOD_PULL_RUNG_1;
		if ( k == 2 )
			dwell = TOD_PULL_RUNG_2;
		else if ( k == 3 )
			dwell = TOD_PULL_RUNG_3;
		else if ( k == 4 )
			dwell = TOD_PULL_RUNG_4;
		wait( ( dwell - TOD_PULL_HITCH ) * sc );

		// the heartbeat: EVERY card does it at EVERY rung, so nobody can tell
		// from it whether the climb stops here. On the LAST rung of a RARE+ the
		// sting replaces the thump - its 0.20 s onset (TOD_REVEAL_LEAD_*) is the
		// hitch, so its body lands on the flip.
		self pull_beat();
		if ( k == reach_at )
		{
			// THE REACH (docs/201 section 4). Its hitch is ALWAYS the plain thump: a sting here would say
			// "it stops" before the reach has played. Then the REACH beat (a second beat at this rung) and the swell.
			self PlayLocalSound( "tod_pull_beat" );
			wait( TOD_PULL_HITCH * sc );
			self pull_beat();
			self PlayLocalSound( "tod_pull_reach" );
			wait( TOD_PULL_REACH * sc );
			if ( reach_win )
				continue;   // BREAK THROUGH: the next rung's push IS the resolution
			// SO CLOSE: a third beat at this rung resolves it, the swell lets go, and the card lands where it was
			// with its own sting (never LEGENDARY: there is no rung above it to reach for)
			self pull_beat();
			self PlayLocalSound( "tod_pull_reach_fail" );
			wait( TOD_PULL_REACH_SETTLE * sc );
			if ( rar >= 2 )
				self PlayLocalSound( "tod_super_sting" );
			wait( TOD_PULL_HITCH * sc );
			continue;
		}
		if ( k == rar && rar >= 4 )
			self PlayLocalSound( "tod_pull_legendary" );
		else if ( k == rar && rar >= 2 )
			self PlayLocalSound( "tod_super_sting" );
		else
			self PlayLocalSound( "tod_pull_beat" );
		wait( TOD_PULL_HITCH * sc );
	}

	// THE FLIP
	if ( rar < 2 )
		self PlayLocalSound( "tod_card_land" );
	self set_field( "todUpg" + slot + "D", domain_id( o.domain ) );

	// A LEGENDARY is announced to everyone else (docs/187: Legendary only).
	if ( rar >= 4 && o.domain != "tier" )
		self announce_legendary();
}

// self = the lucky player. The lobby hears about it: THE TOAST (team_toast, below), in our typeface.
function announce_legendary()
{
	self team_toast( 1, 0, "tod_pull_alert" );
}

// THE TOAST (RT 2026-10-05, the red return; docs/218). The moments the stock IPrintLnBold font announced (it
// dropped across the card deal's banner band, and every letter must be our typeface - user 2026-10-05) go to
// TodToast.lua as ONE int event, drawn in the map's glyph cells on the title plate: ( kind, the player it is
// about (his entity number = client number), code ). LOCKSTEP TodToast.lua (CoD.TodToast.lines):
//   1 <name> PULLED A LEGENDARY            2 <name> PULLED A LEGENDARY <item> (code = the item 1..9)
//   3 <name> IS ON FIRE                    4 CLASS TIER n UNLOCKS AT FLOOR f (code = n * 1000 + f)
//   5 FLOOR f REACHED - CLASS TIER n UNLOCKED (code = n * 1000 + f, + 100000 while the gun still needs a PaP)
//   6 NEW WEAPONS ARE NOT PACK-A-PUNCHED   7 the Archer's arm line
// Three ints: the LuiNotifyEvent shape tod_luck_heat already proves. Free lane: no triggerstring, no clientfield bit.
// self = the player it is about. Every OTHER player sees it (and hears `alert`, when given).
function team_toast( kind, code, alert )
{
	who = self GetEntityNumber();
	sent = 0;
	players = GetPlayers();
	for ( i = 0; i < players.size; i++ )
	{
		p = players[ i ];
		if ( !isdefined( p ) || !isplayer( p ) || p == self )
			continue;
		p LuiNotifyEvent( &"tod_toast", 3, kind, who, code );
		sent++;
		if ( isdefined( alert ) )
			p PlayLocalSound( alert );
	}
	toast_log( "team", kind, who, code, sent );
}

// self = player: a toast for this player alone.
function self_toast( kind, code )
{
	who = self GetEntityNumber();
	self LuiNotifyEvent( &"tod_toast", 3, kind, who, code );
	toast_log( "self", kind, who, code, 1 );
}

// [TOD_TOAST] (dev or diag only, console): every toast sent, so a playtest log shows each moment reached the HUDs.
function toast_log( lane, kind, who, code, sent )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_TOAST] ms=" + GetTime() + " lane=" + lane + " kind=" + kind + " who=" + who + " code=" + code + " sent=" + sent;
	/#
	PrintLn( line );
	#/
}

// self = player. THE HOT STREAK (docs/201 section 5): a deal is ONE pull, counted once its reveal has shown
// it. Its result is the best card it showed (the CLASS TIER card and a floor-locked card do not count; a dev
// CARD TEST card never does). A deferred station deal re-presents the SAME cards after a round event took the
// screen, so the first card carries a latch and the second showing does not count again; a showing that was cut
// off mid-reveal never reached this line, so the re-presentation is the one that counts. The luck module owns
// the streak and is reached through level.tod_luck_streak_fn (it imports this module: the cycle rule).
#define TOD_STREAK_FB_DEAL     0.15   // the heat sound waits this long after the last flip's beat
function streak_report( opts )
{
	if ( !isdefined( opts ) || !isdefined( opts[ 0 ] ) || IS_TRUE( opts[ 0 ].tod_streak_done ) )
		return;
	opts[ 0 ].tod_streak_done = true;
	best = 0;
	for ( i = 0; i < opts.size; i++ )
	{
		o = opts[ i ];
		if ( !isdefined( o ) || IS_TRUE( o.locked ) || o.domain == "tier" || IS_TRUE( o.dev_test ) )
			continue;
		r = reveal_rarity( o );
		if ( r > best )
			best = r;
	}
	self pull_log( "STREAK_REPORT best=" + best + " cards=" + opts.size );
	if ( best < 1 || !isdefined( level.tod_luck_streak_fn ) )
		return;
	[[ level.tod_luck_streak_fn ]]( self, best, "deal", TOD_STREAK_FB_DEAL );
}

// self = player. opts = array of 1-2 option structs (see _tod_upgrades).
// Returns 1 or 2.
function present_choice( opts, timeout )
{
	self endon( "disconnect" );

	self ensure_menu();

	// ---- THE DEAL (v14.52) -------------------------------------------------
	// Cards no longer appear finished. The panel opens on two EMPTY SOCKETS and
	// each slot lands on its own beat — see reveal_deal below for the whole
	// timeline and the field contract it rides.
	//
	// LEVEL is pushed up front (it is invisible until the card lands and the
	// Lua needs it in hand when the domain edge fires). RARITY is pushed as 1
	// up front — "a card is coming here", NOT its true rarity — and re-pushed
	// with the truth at that slot's hold. DOMAIN stays 0 until the card lands;
	// the 0 -> N edge IS the client's "deal this card now" trigger.
	// THE PULL (docs/187). Both slots open as FACE-DOWN BACKS at rung 0 (COMMON)
	// and climb from there; the rarity fields carry the wire value rarity - 1.
	// LEVEL is pushed up front (the Lua needs it in hand when the card lands, to
	// draw the level pips); DOMAIN stays 0 until the card flips - the 0 -> N edge
	// IS the client's "flip this card now" trigger. todUpgSolo says whether a
	// second back is dealt at all.
	self set_field( "todUpgAD", 0 );
	self set_field( "todUpgAR", 0 );
	self set_field( "todUpgAL", opts[ 0 ].cur );
	self set_field( "todUpgBD", 0 );
	self set_field( "todUpgBR", 0 );
	if ( isdefined( opts[ 1 ] ) )
	{
		self set_field( "todUpgBL", opts[ 1 ].cur );
		self set_field( "todUpgSolo", 0 );
	}
	else
	{
		self set_field( "todUpgSolo", 1 );
	}

	// Card readout = the LUCK BAR in tens (0..10 -> "LUCK n0%" in the Lua).
	luck = 0;
	if ( isdefined( self.tod_luck_bar ) )
		luck = int( self.tod_luck_bar / 10 );
	if ( luck > 10 )
		luck = 10;
	self set_field( "todUpgLuck", luck );

	// FOCUS 0 WHILE SHOW IS 1 IS THE REVEAL STATE, and it is unreachable any
	// other way: every other path that sets show=1 sets focus 1..4 in the same
	// breath, and wait_for_choice never writes 0. The Lua keys its whole reveal
	// mode off that pair, so this ordering is a CONTRACT, not an accident.
	self set_field( "todUpgFocus", 0 );
	self set_field( "todUpgTime", int( timeout ) );
	self set_field( "todUpgHold", 0 );
	self.tod_upg_hold_shown = 0;
	self set_field( "todUpgShow", 1 );

	self reveal_deal( opts );
	self streak_report( opts );   // THE HOT STREAK (docs/201): the deal counts once its cards are face up

	// The reveal used todUpgHold as its beat counter; the hold bar must start empty.
	// (A drop is ignored by the Lua, which only reacts to the counter RISING.)
	self set_field( "todUpgHold", 0 );
	self.tod_upg_hold_shown = 0;

	self set_field( "todUpgFocus", 1 );   // left card focused by default

	// The freeze is the CALLER's job now (tod_upgrades::menu_freeze — the
	// soft-freeze: FreezeControls kills ALL input reads, live-test 2026-08-19).

	// THE LOCKED SLOT (v14.39). A CLASS TIER card dealt below its floor gate is
	// shown but cannot be taken — see _tod_upgrades::make_tier_option. Only the
	// RIGHT slot can ever be locked, which is what makes this safe: focus starts
	// on the left card and a timeout locks whatever is focused, so a fully
	// unselectable panel is impossible by construction. (roll_options refuses to
	// deal a lone locked card for the same reason.)
	// v16.79 — the domain test is belt and braces: only make_tier_option and
	// solo_refresh_option ever write .locked, both on the tier struct, and both
	// redeal paths skip the tier card, so nothing else can carry the flag. A
	// lock on anything but the promotion would be a bug; this makes it a
	// non-event instead of a card the player cannot reach.
	locked = 0;
	if ( isdefined( opts[ 1 ] ) && IS_TRUE( opts[ 1 ].locked ) && opts[ 1 ].domain == "tier" )
		locked = 2;

	self.tod_upg_timed_out = false;
	choice = self wait_for_choice( opts, timeout, locked );

	// THE AURA STOPS THE INSTANT THE CHOICE IS MADE, not when the panel hides.
	// It is a retrigger, so what this actually stops is the NEXT pass — the
	// current one plays out, bounded by TOD_AURA_UNIT_SECS, and the 0.7s confirm
	// flash below covers most of that tail. Notifying unconditionally (rather
	// than only when an ultimate was dealt) costs nothing and cannot leave a
	// driver running because a rarity check drifted.
	self notify( "tod_upg_aura_stop" );

	// confirm flash (Lua: chosen card teal, other recedes), then hide
	self set_field( "todUpgFocus", 0 );
	self set_field( "todUpgTime", 0 );
	self set_field( "todUpgShow", ( ( choice == 1 ) ? 2 : 3 ) );
	wait 0.7;
	self set_field( "todUpgShow", 0 );

	return choice;
}

// self = player. MENU-style input (user 2026-08-18): a card is ALWAYS focused
// (left by default, blinking); switch focus with D-PAD LEFT/RIGHT (actionslot
// 3/4), the MOVE STICK / strafe keys, or AIM/FIRE as fallbacks; HOLD JUMP (A /
// space) for 0.5s to lock the focused card in (blink speeds up while held).
// Timeout locks whatever is focused. Controls are frozen — none of these
// inputs leak into gameplay.
// `locked` (v14.39) = a slot index that must never receive focus (0 = none;
// only ever 2, see present_choice). Enforced at the ONE place every input lane
// converges — the `want` -> `sel` commit below — rather than in each of the
// seven lanes that can produce a `want`, so a lane added later cannot bypass it.
// v16.3 — THE DEVICE LATCH NOW ALSO TELLS THE CLIENT (repo review 2026-09-01).
// Both LUI menus used to GUESS the device with Engine.IsGamepadEnabled( 0 ) and
// fell back to CONTROLLER wording, so keyboard players read "HOLD A" — four
// Workshop reports, the last one after the 08-24 keyboard fix. The only
// device-proving input the server has is the d-pad press that arms
// tod_input_pad (see the latch note in wait_for_choice), so the menus now
// default to the KEYBOARD plates (PC-only mod) and flip to the pad plates when
// this fires — over the same zero-bit int-notify lane as tod_upg_sync, so no
// clientfield bit is spent. Sent ONCE per player (the latch is one-way); the
// per-life reopen in player_lui_life resends it. _tod_class_select inlines the
// same three lines (it does not import this module).
function pad_latch()   // self = player
{
	if ( IS_TRUE( self.tod_input_pad ) )
		return;
	self.tod_input_pad = true;
	self LuiNotifyEvent( &"tod_input_pad", 1, 1 );
}

function wait_for_choice( opts, timeout, locked )
{
	self endon( "disconnect" );

	if ( !isdefined( locked ) )
		locked = 0;

	two = isdefined( opts[ 1 ] );
	sel = 1;         // focused card: 1 left, 2 right
	held = 0;
	phase = 0;       // blink phase 0/1
	blink_t = 0;
	last_focus = 0;
	last_secs = int( timeout );
	last_strafe = 0; // KBM strafe edge latch (v10.3)
	last_fwd = 0;    // KBM W/S edge latch (v10.18 — full-WASD, user 2026-08-24)
	// v10.19 (user retest: "Controller works fine but keyboard still does
	// nothing"): the whole KBM lane so far rides GetNormalizedMovement + the
	// jump read, and NEITHER has ever been live-verified on a keyboard — map
	// 1's freeze lesson and every menu test since were controller runs. So the
	// menu now ALSO listens on reads the engine core exercises constantly and
	// that a keyboard definitely owns: MOUSE1 = left card, MOUSE2 = right card
	// (weapons are DisableWeapons'd for every choice — player_choice_flow wraps
	// present_choice in menu_freeze — so the press cannot fire the gun), and
	// HOLD USE [F] locks alongside JUMP. On controller these add RT/LT/X as
	// bonus inputs, which is harmless.
	// SEEDED latches: attack/ads are sampled ONCE before the loop so a button
	// already held when the panel opens (RT mid-fight) cannot flip focus on the
	// first tick. USE gets the jump treatment (arm-on-release) because the
	// STATION is opened by hold-F — without arming, the buy hold would
	// insta-lock the left card.
	// v10.20 — THE ACTUAL KEYBOARD LANE, and why it is these four buttons.
	// RESEARCH RESULT (workflow 2026-08-24, five parallel source audits):
	//   * ActionSlotThree/Four ARE THE CONTROLLER D-PAD, provably — stock maps
	//     them at util_shared.gsc:2404 ( _button_funcs[ BUTTON_RIGHT ] =
	//     &ActionSlotFourButtonPressed ). BO3 PC binds NO keyboard key to an
	//     action slot in zombies, so on a keyboard they are permanently false.
	//     That is the whole "controller works, keyboard does nothing" report:
	//     the working input was always the D-PAD.
	//   * GetNormalizedMovement is documented as "the player's MOVEMENT
	//     normalized" — not the movement INPUT — and every card flow wraps this
	//     in menu_freeze(), which pins SetMoveSpeedScale to 0.001. A
	//     movement-derived read under a 0.001 pin is ~0 FOR BOTH DEVICES. It is
	//     kept below as a free bonus lane, but nothing depends on it, and
	//     Treyarch never calls it anywhere in share/raw.
	// SO THE LANE IS ACTION BUTTONS, which BOTH devices bind by default. The
	// precedent is the author's OWN SHIPPED CODE: map 1's leaderboard consent
	// card (_acc_leaderboard.gsc:588-596) is an in-game hold-to-choose picker
	// driven by MeleeButtonPressed + AdsButtonPressed, played on keyboard.
	// FOUR buttons, not two, deliberately: menu_freeze calls DisableWeapons(),
	// and if that ever suppresses the attack/ads reads, MELEE and RELOAD are an
	// independent path to the same result. Redundancy is the point.
	last_atk = ( ( self AttackButtonPressed() ) ? 1 : 0 );
	last_ads = ( ( self AdsButtonPressed() ) ? 1 : 0 );
	last_mel = ( ( self MeleeButtonPressed() ) ? 1 : 0 );
	last_rld = ( ( self ReloadButtonPressed() ) ? 1 : 0 );
	// v16.57 THE OFFHAND PAIR (see the lane in the loop): seeded like the rest.
	last_sec = ( ( self SecondaryOffhandButtonPressed() ) ? 1 : 0 );
	last_frag = ( ( self FragButtonPressed() ) ? 1 : 0 );
	use_armed = 0;
	probe_t = 0;     // dev input probe cadence
	// (The v10.19 LUI keyboard bridge was REMOVED in v10.20 — see the input
	// research note at the latch block above. It never had a precedent: every
	// OpenLUIMenu menu in stock, in map 1 and in this map is display-only, and
	// a HUD-layer menu is not on the focused menu stack, so its button
	// callbacks were never dispatched to. Replaced by the action-button lane.)
	last_d3 = 0;     // d-pad edge latches (v10.4; PER SLOT since v16.81): level
	last_d4 = 0;     // reads re-asserted a held direction every tick and snapped
	                 // focus back against a fresh strafe flip (audit find)
	// JUMP RELEASE GATE (co-op audit 2026-08-23): the loop samples
	// JumpButtonPressed() with no press-edge, so a player ALREADY holding jump
	// when the panel opens accumulates `held` from frame one and auto-locks the
	// left card ~0.3s later, before they have read either option. That is not a
	// corner case: menu_freeze uses AllowJump(false), which suppresses the hop
	// but NOT the button read, and the round-1 event drops its cards while
	// players who locked their class early are free-running the base. The
	// personal station is worse — the world is not paused there, so a dodge-hop
	// mid-fight pays for a card. Holds only count once we have seen the button
	// RELEASED at least once, so a press must start after the panel is up.
	jump_armed = 0;
	waited = 0;
	// v16.79 — A CRAWLER DEALT CARDS KEEPS THE PANEL (user 2026-09-03: "sometimes
	// I get two options for upgrades but i cant select one of them"). v15
	// (2026-08-31) let last-stand players into round events, but the mid-card
	// release below had no notion of "already down when the panel opened": for
	// a crawler it fired on the FIRST tick — cards landed, focus on the left
	// card, 50 ms later the loop fell out to the timeout exit — card A taken,
	// card B never reachable, panel gone inside a second. The release exists
	// to undo menu_freeze's DisableWeapons for a player who went down DURING
	// the pick, and menu_freeze never freezes a player who is already down, so
	// for a crawler there is nothing to release. Latch the entry state; break
	// only on the alive -> down transition.
	down_at_open = ( self laststand::player_is_in_laststand() );

	while ( waited < timeout )
	{
		// countdown readout (whole seconds, only on change)
		secs = int( timeout - waited + 0.999 );
		if ( secs != last_secs )
		{
			self set_field( "todUpgTime", secs );
			last_secs = secs;
		}

		// WENT DOWN MID-CARD -> RELEASE THEM NOW (live-report audit 2026-08-26).
		//
		// THE CALLER'S menu_freeze STILL HOLDS DisableWeapons(), AND STOCK NEVER
		// UNDOES IT. This is the whole reason this guard exists, and it is worth
		// stating precisely because it is counter-intuitive: stock's last-stand
		// path does NOT use DisableWeapons at all — it uses DisableWeaponCycling
		// (_zm_laststand.gsc:290) and restores with EnableWeaponCycling +
		// EnableOffhandWeapons (:369-403). Nothing on the down, bleedout or
		// revive path ever calls EnableWeapons(). So a player who goes down
		// while the cards are up is handed the last-stand pistol by
		// _zm.gsc:2826-2892 (GiveWeapon + SwitchToWeapon), holds it on screen,
		// AND CANNOT FIRE IT — for up to TOD_UPG_CHOICE_TIMEOUT + the 0.7s
		// confirm flash. Stock itself uses DisableWeapons this way as a firing
		// lock (_zm.gsc:4855, playerzombie_downed_state).
		//
		// menu_freeze's own laststand check (_tod_upgrades.gsc:1087) is a
		// ONE-SHOT ENTRY test — it refuses to freeze someone already down, and
		// never looks again. This is the other half of that rule.
		//
		// REACHABLE despite the world being paused: the pause freezes AI, but
		// the Panzer's FLAMETHROWER BURN is stock _burnplayer.gsc's own per-player
		// damage loop and knows nothing about level.tod_upgrade_pause, so it keeps
		// ticking (_tod_bosses.gsc records the same exemption for the through-wall
		// shield). Panzers land every 5th round, events every 4th, and the
		// endless-rounds twist starts the next round while the last one's Panzer
		// is still alive — so the overlap is routine, not freak. A Protector
		// rocket already in flight and an in-flight melee notetrack do it too.
		//
		// `break`, NOT `return`: it falls into the existing timeout exit below
		// (tod_upg_timed_out = true; return sel), so no new exit path is created
		// and the caller still unfreezes on return. THE UPGRADE IS NOT
		// FORFEITED — apply_upgrade only refuses a timed-out TIER card, and
		// player_choice_flow already falls back to the other card; a domain card
		// pays out normally. Refusing a tier promotion mid-crawl is exactly the
		// rule the station path already enforces.
		// (v16.79: TRANSITION only — a player down at open keeps the panel; see
		// down_at_open above.)
		if ( !down_at_open && ( self laststand::player_is_in_laststand() ) )
			break;
		// A crawler who BLEEDS OUT mid-pick has no panel any more (the engine
		// closes a player's LUI menus on death -> spectate) — release the event
		// rather than hold the world for a card nobody can answer. IsAlive is
		// TRUE in last stand (stock contract), so this is the dead test alone.
		if ( !isalive( self ) )
			break;

		// --- focus switching: D-PAD ONLY ------------------------------------
		// User 2026-08-21: "change the controls of the upgrade menu to only
		// use the dpad". ActionSlotThree/Four ARE the d-pad left/right reads.
		// The old ADS/FIRE and movement-stick fallbacks are gone — with the
		// personal station no longer freezing the player, strafing to dodge
		// was silently flipping the card, and aiming/firing to fight was
		// selecting one.
		//
		// ...and then v10.19/v10.20 put every one of those lanes BACK, because
		// a keyboard has no d-pad. v14.20 (user 2026-08-30: "can we make the
		// upgrade menu d pad only on controller. Its akward to move around and
		// still set an upgrade") reconciles the two directives instead of
		// picking one: the extra lanes now live behind a PER-PLAYER DEVICE
		// LATCH, so the pad gets the 2026-08-21 rule and the keyboard keeps the
		// 2026-08-24 one.
		//
		// HOW THE LATCH KNOWS. There is NO server-side device read in T7 — no
		// gamepad builtin exists anywhere in share/raw, and CSC/LUI cannot
		// answer the server (clientfields are one-way). What the map DOES have
		// is an input that only one device can produce: ActionSlotThree/Four
		// are the controller d-pad and BO3 PC binds no keyboard key to an
		// action slot in zombies (the v10.20 research). So the FIRST d-pad
		// press this player ever makes proves the device, and tod_input_pad
		// latches for the rest of the match (a plain player field — it rides
		// the player entity, so it survives respawns like tod_levels does, and
		// _tod_class_select sets the same field, which is what usually gets it
		// latched during the 30s draft, before the round-1 event opens).
		// ONE-WAY, deliberately: the d-pad is never gated on anything, so a
		// player who somehow bound a key to an action slot still navigates with
		// it, and a player who never touches the d-pad simply keeps every lane
		// they had before this change. Nothing regresses for the keyboard.
		//
		// ⚠️ v16.81 (2026-09-03) — THE PREMISE ABOVE IS FALSE. The player's own
		// <game>/players/bindings_0.cfg reads:
		//     bind 1 "+actionslot 1"   bind 2 "+actionslot 2"
		//     bind 3 "+actionslot 4"   bind 4 "+actionslot 3"
		// so keyboard 3 / 4 ARE action-slot presses (4 and 3, swapped). A KBM
		// player who taps 3 or 4 during the draft or a deal used to be latched
		// as a pad for the rest of the match and lose every keyboard lane —
		// "frozen" with two cards up. tod_input_pad therefore means "an
		// action-slot press was seen", not "this is a controller", and its
		// blast radius is now the STATION only: at a ROUND EVENT (the world
		// paused, movement pinned, weapons disabled) every lane is live for
		// everyone — there is no fight to be awkward with, which was the whole
		// point of the 2026-08-30 d-pad-only rule. The station keeps that rule.
		want = sel;
		// v16.81 (user 2026-09-03: "my dpad was frozen. And another player
		// reported this too") — PER-SLOT edges, read INDEPENDENTLY. The old
		// `else if` let a slot-3 read that stays true hide slot 4 for the whole
		// panel: no edge, no right card. Stock binds slot 3 to the held weapon's
		// altMode (_zm.gsc:1836), so its read is the one most exposed to weapon
		// state. Each slot now latches on its own; either still seeds the
		// action-slot latch below.
		d3 = ( ( self ActionSlotThreeButtonPressed() ) ? 1 : 0 );
		d4 = ( ( self ActionSlotFourButtonPressed() ) ? 1 : 0 );
		if ( d3 || d4 )
			self pad_latch();   // an action-slot press was seen — see the latch note above (not a device PROOF; v16.81)
		if ( d3 && !last_d3 )
			want = 1;   // edge-latched (v10.4) — a fresh press only
		if ( d4 && !last_d4 )
			want = 2;
		last_d3 = d3;
		last_d4 = d4;
		// v16.57 THE OFFHAND PAIR — TACTICAL = LEFT card, LETHAL = RIGHT card, on
		// BOTH devices, always live (user 2026-09-02: "Left bumper goes right and
		// right goes left"). The fire/aim pair can NEVER be given a side that is
		// right on both devices: every pad layout puts FIRE on the right hand and
		// AIM on the left (default RT/LT, the user's own bumper layout RB/LB),
		// while a mouse puts fire on the LEFT button — and the server cannot tell
		// the devices apart (bo3-menu-input-apis fact 4). The grenade pair has no
		// such problem: every BO3 layout keeps TACTICAL on the left-hand button and
		// LETHAL on the right-hand one (default LB/RB; bumper-swapped LT/RT), so
		// "tactical = left, lethal = right" is physically correct on every pad by
		// construction, and on a keyboard it is a stable key pair the plate names
		// through its bind tokens. NOT gated on the pad latch: nobody holds a
		// grenade button while fighting, and menu_freeze holds
		// DisableOffhandWeapons() so a press here can never throw one. Fire/aim
		// no longer move focus at all (they were the reversed lane).
		sec = ( ( self SecondaryOffhandButtonPressed() ) ? 1 : 0 );
		frg = ( ( self FragButtonPressed() ) ? 1 : 0 );
		if ( sec && !last_sec )
			want = 1;
		else if ( frg && !last_frag )
			want = 2;
		last_sec = sec;
		last_frag = frg;
		// EVERY LANE BELOW IS KEYBOARD-ONLY (v14.20). On a controller these are
		// the strafe stick, RT, LT, R3 and X — i.e. exactly the buttons a player
		// is holding while fighting at the personal upgrade station, which is
		// the awkwardness the user reported. The reads are SKIPPED, not merely
		// ignored, so the per-source latches below stay untouched and cannot
		// fire a stale edge if the flag were ever cleared.
		// Seeded OUTSIDE the gate because the dev input probe at the bottom of
		// the loop prints all four every second — skipping the reads must not
		// hand it uninitialised variables (dev-only, but a dev build is exactly
		// where this would be discovered the hard way).
		atk = 0;
		ads = 0;
		mel = 0;
		rld = 0;
		// v16.81: the latch gates these lanes at the STATION only (world live,
		// the player is fighting — the awkward case). At a ROUND EVENT the
		// world is paused and the player cannot move or shoot, so every lane
		// stays live for every device: a pad whose d-pad read has died still
		// has R3 / X, and a KBM player falsely latched by keyboard 3/4 still
		// has WASD / R / V. See the latch note above.
		// v16.84 narrows "the STATION" to a CO-OP station without touching this
		// line: a solo pick now sets level.tod_upgrade_pause itself, so it takes
		// the paused branch and every lane opens. That is the rule above being
		// obeyed, not bypassed — the d-pad-only gate was earned by the player
		// being mid-fight, and a frozen solo buyer is not.
		if ( !IS_TRUE( self.tod_input_pad ) || IS_TRUE( level.tod_upgrade_pause ) )
		{
		// KBM (playtest 2026-08-23: "Make sure KBM can pick the cards and
		// upgrades"): ActionSlot 3/4 are the D-PAD reads — a keyboard player
		// had NO way to move focus. A/D (the strafe axis; left stick on pad)
		// now switches too, EDGE-LATCHED like the class draft: only a FRESH
		// push flips, so holding a strafe to dodge flips once, not per-tick.
		// That per-tick flipping is what got the stick read removed on
		// 2026-08-21 — the latch is the difference, and KBM access outranks
		// the residual single flip (user directive).
		strafe = 0;
		mv = self GetNormalizedMovement();
		if ( isdefined( mv ) )
		{
			if ( mv[ 1 ] < -0.4 )
				strafe = -1;
			else if ( mv[ 1 ] > 0.4 )
				strafe = 1;
		}
		if ( strafe != 0 && strafe != last_strafe )
			want = ( ( strafe < 0 ) ? 1 : 2 );
		last_strafe = strafe;
		// FULL WASD (user 2026-08-24, from beta comments: "the upgrade menu
		// needs to be fully keyboard accessable. WASD, up left down right").
		// W/S = the forward axis (mv[0]); with exactly TWO cards side by side
		// there is no "up card", so a fresh W or S press flips focus to the
		// OTHER card — every direction key now moves focus, none is dead.
		// Same PER-SOURCE edge latch as the strafe (the draft's cross-fire
		// lesson): sign is irrelevant to a flip, so W-vs-S never inverts.
		// ARROW KEYS ride this same read, but only for players whose arrows
		// are BOUND to movement — GSC has no raw-key read, so unbound arrows
		// are invisible to script. WASD is the guaranteed lane.
		fwd = 0;
		if ( isdefined( mv ) )
		{
			if ( mv[ 0 ] < -0.4 )
				fwd = -1;
			else if ( mv[ 0 ] > 0.4 )
				fwd = 1;
		}
		if ( fwd != 0 && fwd != last_fwd )
			want = ( ( sel == 1 ) ? 2 : 1 );
		last_fwd = fwd;
		// ACTION BUTTONS (v10.20) — the keyboard lane. All edge-latched and
		// pre-seeded (see the latch block above), so a button already held when
		// the panel opens cannot flip focus on tick one.
		//   (fire / aim: READ for the dev probe only since v16.57 — no longer a
		//   lane; the offhand pair above is the directional one on every device)
		//   MELEE (V / R3)   -> flip to the other card
		//   RELOAD (R / X)   -> flip to the other card
		atk = ( ( self AttackButtonPressed() ) ? 1 : 0 );
		ads = ( ( self AdsButtonPressed() ) ? 1 : 0 );
		mel = ( ( self MeleeButtonPressed() ) ? 1 : 0 );
		rld = ( ( self ReloadButtonPressed() ) ? 1 : 0 );
		if ( ( mel && !last_mel ) || ( rld && !last_rld ) )
			want = ( ( sel == 1 ) ? 2 : 1 );
		last_mel = mel;
		last_rld = rld;
		}   // end keyboard-only lanes (v14.20 device latch)
		if ( !two )
		{
			if ( IS_TRUE( level.tod_dev ) && want == 2 )
				self tod_quiet_print_to( "^3card 2 refused: single-card deal" );
			want = 1;
		}
		// THE LOCKED SLOT REFUSES FOCUS (v14.39). Every input lane above funnels
		// into `want`; this is the single commit point, so one test covers the
		// d-pad, the movement stick, all four action buttons and the KBM lanes.
		//
		// AUDIBLE, because a control that silently does nothing reads as a
		// broken trigger — the same rule the pause-gated devices already follow.
		// It can only fire on an input EDGE (want only differs from sel when a
		// lane produced a change this tick), so holding a direction against the
		// locked card cannot machine-gun the deny sound.
		//
		// PlaySound, NOT PlayLocalSound, and that is deliberate. Every
		// PlayLocalSound in this map pairs with a CUSTOM tod_* alias; the only
		// proven pairing for this STOCK alias is `PlaySound( "zmb_no_purchase" )`
		// — four live call sites in _tod_ammo_crate. PlayLocalSound with it
		// would be the first caller of an untested combination, and its failure
		// mode is SILENCE, which is precisely the thing this sound exists to
		// prevent. (Caught by grepping for a precedent and finding only my own
		// new line — a self-citation is not a precedent.)
		if ( locked > 0 && want == locked )
		{
			want = sel;
			self PlaySound( "zmb_no_purchase" );
			// DEV: name the refused slot's domain — a refusal that names nothing
			// is the 2026-09-03 report ("a sprint card I couldn't switch to").
			if ( IS_TRUE( level.tod_dev ) )
				self tod_quiet_print_to( "^3card " + locked + " refused: locked " + opts[ locked - 1 ].domain );
		}
		if ( want != sel )
		{
			sel = want;
			held = 0;   // switching resets any lock progress
			phase = 0;
			blink_t = 0;
			self PlayLocalSound( "tod_ui_tick" );   // focus moved
		}

		// --- hold JUMP or USE to lock (v10.19: USE [F] joins for KBM) -------
		// Each button arms on its own first RELEASE (jump: pre-open hops; use:
		// the station is BOUGHT with hold-F, so the same finger is still down
		// when this panel opens). An armed hold on EITHER accumulates.
		b_jump = self JumpButtonPressed();
		b_use = self UseButtonPressed();
		if ( !b_jump )
			jump_armed = 1;
		if ( !b_use )
			use_armed = 1;
		if ( ( b_jump && jump_armed ) || ( b_use && use_armed ) )
		{
			held += 0.05;
			if ( held >= TOD_UPG_HOLD_SECS )
			{
				self set_field( "todUpgHold", 15 );
				self PlayLocalSound( "tod_ui_lock" );
				return sel;
			}
		}
		else
		{
			held = 0;
		}

		// DEV INPUT PROBE (v10.19): one line per second of exactly what the
		// server reads from this player — the tool that ends the "keyboard
		// does nothing" guessing. Read it off a KEYBOARD run: whichever
		// column stays 0 while the key is held is the dead read.
		if ( IS_TRUE( level.tod_dev ) )
		{
			probe_t += 0.05;
			if ( probe_t >= 1.0 )
			{
				probe_t = 0;
				mvp = self GetNormalizedMovement();
				fwd_p = 0;
				str_p = 0;
				if ( isdefined( mvp ) )
				{
					fwd_p = int( mvp[ 0 ] * 10 );
					str_p = int( mvp[ 1 ] * 10 );
				}
				// v16.81: every lane's raw read PLUS the loop's own state, so a
				// "frozen d-pad" repro says which it is in one line: d3/d4 stuck
				// at 0 while held = the engine is not delivering the slot; d4=1
				// with sel stuck = the lane; sel moving while the HUD does not =
				// the Lua. Read it off a dev run with the panel up.
				self tod_quiet_print_to( "^3inp mv=" + fwd_p + "," + str_p
					+ " j=" + ( ( b_jump ) ? 1 : 0 ) + " u=" + ( ( b_use ) ? 1 : 0 )
					+ " m1=" + atk + " m2=" + ads + " mel=" + mel + " rld=" + rld
					+ " d3=" + d3 + " d4=" + d4 + " tac=" + sec + " let=" + frg
					+ " | sel=" + sel + " two=" + ( ( two ) ? 1 : 0 ) + " lock=" + locked
					+ " pad=" + ( ( IS_TRUE( self.tod_input_pad ) ) ? 1 : 0 )
					+ " ev=" + ( ( IS_TRUE( level.tod_upgrade_pause ) ) ? 1 : 0 ) );
			}
		}

		// hold-progress fill (0..15) — the bar under the focused card
		hv = int( held / TOD_UPG_HOLD_SECS * 15 );
		if ( hv > 15 )
			hv = 15;
		if ( !isdefined( self.tod_upg_hold_shown ) || self.tod_upg_hold_shown != hv )
		{
			self set_field( "todUpgHold", hv );
			self.tod_upg_hold_shown = hv;
		}

		// --- focus blink (faster while locking) ----------------------------
		blink_t += 0.05;
		interval = ( ( held > 0 ) ? ( TOD_UPG_BLINK_SECS * 0.5 ) : TOD_UPG_BLINK_SECS );
		if ( blink_t >= interval )
		{
			blink_t = 0;
			phase = 1 - phase;
		}

		focus = ( ( sel == 1 ) ? ( ( phase == 0 ) ? 1 : 2 ) : ( ( phase == 0 ) ? 3 : 4 ) );
		if ( focus != last_focus )
		{
			self set_field( "todUpgFocus", focus );
			last_focus = focus;
		}

		wait 0.05;
		waited += 0.05;
	}

	self.tod_upg_timed_out = true;
	return sel;   // timeout — lock whatever is focused
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
