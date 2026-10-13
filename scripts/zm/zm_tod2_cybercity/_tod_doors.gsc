// =============================================================================
// _tod_doors.gsc — buyable stairwell doors.
//
// THE MAP 1 LESSON (do not re-learn): a generator-written zombie_door
// trigger_use is DEAD — the zone system re-disables it and a map brush entity
// has no usable .origin (reports 0,0,0). So: disable the map trigger, spawn a
// trigger_radius_use on BOTH sides of the doorway (the slab occludes a single
// center trigger from the approach side), and drive the buy in script: charge
// points, set the zone script_flag, hide+notsolid+connectpaths the slab.
// Script-spawned use triggers REQUIRE TriggerIgnoreTeam() or no prompt shows.
// Slab starts Solid()+DisconnectPaths() (navmesh ignores entity collision).
//
// Doorway coordinates come from the GENERATED _tod_door_data.gsc (emitted by
// tools/gen_tower_map.js from the same tables that cut the .map — no drift).
// =============================================================================

#using scripts\shared\flag_shared;
#using scripts\zm\_zm;          // get_zombie_count_for_round (door price scaling)
#using scripts\zm\_zm_score;
#using scripts\zm\_zm_utility;
#using scripts\zm\zm_tod2_cybercity\_tod_door_data;
#using scripts\zm\zm_tod2_cybercity\_tod_luck;   // door buys pay luck (v5)
#using scripts\zm\zm_tod2_cybercity\_tod_perk_scatter;   // v16.11: derez_burst on the door slide (import graph cycle-free — docs/61 verified perk_scatter never reaches _tod_doors)

#insert scripts\shared\shared.gsh;

// v16.11 — DOOR GATES THAT OPEN (facelift §2; the frame geometry is
// gen_tower_map.js DOORS `gate`). A lap door no longer blinks away: on the buy
// the slab SLIDES INTO THE CORE like a pocket door — MoveX toward x=0 by
// TOD_DOOR_SLIDE_DIST (the slab is 160 wide; 168 puts it fully inside the
// 512-square core, which is solid, so it is never seen again even before the
// Hide) over TOD_DOOR_SLIDE_SECS, with the map's own de-rez burst at the
// doorway and stock's heavy-door cue (the alias _zm_blockers plays for every
// stock door, so it is in every zombies sound bank). The slab stays Solid and
// the paths stay cut until the slide ends, then the old Hide / NotSolid /
// ConnectPaths sequence runs unchanged — every consumer of "the door is open"
// sees exactly what it saw before, TOD_DOOR_SLIDE_SECS later. LAP DOORS ONLY: the roof,
// power and bay slabs sit in other walls and keep the instant open.
// TOD_DOOR_SLIDE 0 restores the blink for every door (-GscOnly).
// v16.56 (user 2026-09-02: "the sliding doors ... need to be a bit quicker.
// People will get annoyed and die from it moving too slow"): 1.2 -> 0.5 s.
// THE SLAB IS SOLID FOR THE WHOLE SLIDE (Hide/NotSolid/ConnectPaths only run
// on movedone), so the slide length IS a wall the buyer stands at with the
// horde behind them — every tenth of a second here is paid at the door.
#define TOD_DOOR_SLIDE        1
#define TOD_DOOR_SLIDE_DIST   168
#define TOD_DOOR_SLIDE_SECS   0.5
#define TOD_DOOR_SLIDE_SOUND  "zmb_heavy_door_open"
// PLAYED ON A CARRIER (2026-10-05): zm_utility::play_sound_at_pos looks the name up in
// level.zombie_sounds, which this map never filled for it (stock maps add_sound it themselves;
// the usermap template does not), so every slide and the unseal cue hit its AssertMsg + return
// and played NOTHING. tod_perk_scatter::play_sound_at_origin is the Fall seal's lane for the same
// alias; init logs SoundGetPlaybackTime for it so a run proves it is loaded. THE 2026-10-05 17:33
// RUN LOGGED ms=-1: the stock alias is NOT in this usermap's banks, so the map now defines
// zmb_heavy_door_open itself (sound/aliases/tod_ui.csv: an original BO1 hydraulic door start,
// sound_assets/tod/doors/). The Fall's crown seal plays the same alias and gains it too.

#namespace tod_doors;

function init()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	wait 1;   // let stock door_init finish (it flag::init's the script_flags we set on purchase)
	broken_routes_init();

	cue_ms = SoundGetPlaybackTime( TOD_DOOR_SLIDE_SOUND );
	if ( !isdefined( cue_ms ) )
		cue_ms = -1;
	seal_log( "CUE alias=" + TOD_DOOR_SLIDE_SOUND + " ms=" + cue_ms + " (ms <= 0: not loaded, the doors slide silently)" );

	doors = GetEntArray( "zombie_door", "targetname" );
	for ( i = 0; i < doors.size; i++ )
	{
		if ( isdefined( doors[ i ] ) )
			level thread door_buy_setup( doors[ i ] );
	}

	// Set LAST: the dev harness (_tod_main::dev_crown_test) waits on this before
	// calling dev_open_all_doors, so it cannot race the setup above and find
	// slabs that have not been made Solid()/DisconnectPaths() yet — it would
	// then "open" a door that promptly closes itself.
	level.tod_doors_ready = true;
}

function door_buy_setup( d )
{
	level endon( "end_game" );

	cost = 1000;
	if ( isdefined( d.zombie_cost ) )
		cost = int( d.zombie_cost );

	slab = undefined;
	if ( isdefined( d.target ) )
		slab = GetEnt( d.target, "targetname" );

	flag = "";
	if ( isdefined( d.script_flag ) )
		flag = d.script_flag;

	info = tod_door_data::get_door_info( flag );
	if ( !isdefined( info ) )
		return;   // unknown door — leave it alone rather than break it

	// v9.41: the PRICE rides in the generated data file too (the same generator
	// table writes the .map's zombie_cost) and WINS over the map entity — the
	// entity value is frozen into the BSP at cod2map time, so without this a
	// price change needed a full geometry build. Map value = fallback only.
	if ( isdefined( info.cost ) )
		cost = int( info.cost );

	if ( isdefined( slab ) )   // barrier solid + nav cut until bought
	{
		slab Solid();
		slab DisconnectPaths();
	}

	d TriggerEnable( false );   // the dead map trigger; our spawned ones drive the buy
	d.tod_bought = false;
	d.tod_trigs = [];
	// v13.9: kept on the ent + a flag-keyed registry so force_open_by_flag can
	// run the open path without the buy closure's locals.
	d.tod_slab = slab;
	d.tod_flag = flag;
	// v16.11: the slide. Lap doors sit on the east flight (org x=+336, odd
	// floors) or the west flight (x=-336, even floors); "into the core" is
	// toward x=0 either way. Only enter_lapN doors slide (see the header).
	d.tod_org = info.org;
	d.tod_is_lap = IsSubStr( flag, "enter_lap" );
	d.tod_slide_dx = ( ( info.org[ 0 ] > 0 ) ? -TOD_DOOR_SLIDE_DIST : TOD_DOOR_SLIDE_DIST );
	if ( flag != "" )
	{
		if ( !isdefined( level.tod_doors_by_flag ) )
			level.tod_doors_by_flag = [];
		level.tod_doors_by_flag[ flag ] = d;
	}

	spawn_buy_trigger( d, info.org + info.off, cost, slab, flag, info.dest );
	spawn_buy_trigger( d, info.org - info.off, cost, slab, flag, info.dest );
	level thread haven_seal_watch( d );
}

// THE SEALED WAY DOWN (user 2026-10-04, the first real playthrough: "You must secure the dome
// area before you move on or else door cannot be bought"). A haven floor's way down - the
// enter_lap<floor> door at the foot of its hall's W flight - is SEALED while that floor's haven
// is live and not yet taken. _tod_haven owns the question (level.tod_haven_door_seal_fn: -1 not
// a haven door, 1 sealed, 0 buyable); this module owns the prompt and the refusal (the buy loop
// re-asks it on every press). Field-read, no import either way.
// THE PROMPT costs ONE triggerstring slot (one constant for all four doors); the way back is the
// trigger's OWN spawn-time string, rebuilt from the dest + price it was minted with, so the
// unseal never mints a new one (lint_tod_hints counts the same template once).
function haven_seal_watch( d )
{
	level endon( "end_game" );
	wait 0.5;   // _tod_haven::init publishes the hook at load; the doors wake a second after the blackscreen
	if ( !isdefined( level.tod_haven_door_seal_fn ) || !isdefined( d.tod_flag ) || d.tod_flag == "" )
		return;
	if ( [[ level.tod_haven_door_seal_fn ]]( d.tod_flag ) < 0 )
		return;   // not a haven floor's way down
	sealed = false;
	while ( !IS_TRUE( d.tod_bought ) )
	{
		want = ( [[ level.tod_haven_door_seal_fn ]]( d.tod_flag ) == 1 );
		if ( want != sealed )
		{
			sealed = want;
			d.tod_sealed = want;
			for ( i = 0; i < d.tod_trigs.size; i++ )
			{
				t = d.tod_trigs[ i ];
				if ( !isdefined( t ) )
					continue;
				if ( want )
					t SetHintString( "Open Door - SEALED - Secure the dome on this floor first" );
				else if ( isdefined( t.tod_hint_dest ) )
					t SetHintString( "Hold ^3[{+activate}]^7 Open Door to " + t.tod_hint_dest + " ^2[Cost: " + t.tod_hint_price + "]" );
			}
			seal_log( ( want ? "SEALED" : "UNSEALED" ) + " flag=" + d.tod_flag + " round=" + level.round_number );
			if ( !want && isdefined( d.tod_org ) )
				tod_perk_scatter::play_sound_at_origin( d.tod_org, TOD_DOOR_SLIDE_SOUND, 4 );   // the way down unlocks: the heavy door's cue at it
		}
		wait 0.5;
	}
}

// [TOD_DOOR_SEAL] console-only (dev or diag): the seal's state changes and every refused press.
function seal_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_DOOR_SEAL] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// ---------------------------------------------------------------------------
// DOOR PRICE SCALING (user 2026-08-23: "Door cost should scale with amount of
// zombies spawning", answering the co-op audit finding that a quad team splits
// a 186,975-point door ladder four ways while earning roughly four times the
// points — so bigger teams climbed far higher per round than solo).
//
// THE MULTIPLIER IS THE ZOMBIE RATIO, exactly as asked: how many zombies a
// round spawns at the current player count divided by how many it would spawn
// solo. Stock adds zombie_ai_per_player (6) per extra player, so this lands
// near 1.0 / 1.5 / 2.0 / 2.5 and MOVES WITH stock's own curve rather than a
// table we would have to keep in sync.
//
// EVALUATED AT A FIXED REFERENCE ROUND, not the live one. The ratio drifts with
// the round number, and a price that climbed every round would fight the
// generator's +100/lap ladder and make late doors unbuyable — the ask was to
// scale with PARTY SIZE (which is what changes the zombie count), not to make
// doors inflate over time.
//
// Solo is untouched by construction (ratio 1.0), which matters: the door ladder
// was tuned solo and the user has been testing it solo.
// REF ROUND IS THE TUNING KNOB, and it matters more than it looks — stock's
// curve steepens with the round, so the same formula gives very different
// multipliers depending where you sample it (quad: x1.56 at r5, x2.36 at r10,
// x4.00 at r20, x4.86 at r30).
//
// Round 10 gives  solo x1.00 / duo x1.27 / trio x1.82 / quad x2.36
//   -> the 186,975-point ladder becomes ~441k for a quad, about 110k a head
//      against solo's 187k. So a big team still has it easier per player on
//      PROGRESSION (which is right — they are fighting a tougher horde), but
//      nothing like the 4x free ride the audit found.
// Sampling at r20 would make quad per-capita exactly equal to solo. That is
// "fairer" on paper and probably too harsh in play, since co-op ALSO now eats
// scaled zombie health and a higher AI cap. Move this if the beta says so.
#define TOD_DOOR_SCALE_REF_ROUND  10

function door_cost_mult()
{
	players = GetPlayers();
	n = players.size;
	if ( n < 2 )
		return 1.0;                     // solo: exactly the authored price

	solo = zm::get_zombie_count_for_round( TOD_DOOR_SCALE_REF_ROUND, 1 );
	many = zm::get_zombie_count_for_round( TOD_DOOR_SCALE_REF_ROUND, n );
	if ( !isdefined( solo ) || solo < 1 || !isdefined( many ) || many < 1 )
		return 1.0;                     // stock said something odd — never invent a price

	m = many / ( solo * 1.0 );
	if ( m < 1.0 )
		m = 1.0;                        // a door may never get CHEAPER in co-op
	return m;
}

// The price a door asks RIGHT NOW. Kept as a function rather than a number
// baked at spawn because players connect and drop mid-game, so the CHARGE has
// to be re-read at the moment of purchase (buy_trigger_wait, below).
//
// THE HINT READS THIS ONCE, AT SPAWN. Hint and charge can therefore disagree
// after a party-size change; that is deliberate and the reasoning is in the
// block above buy_trigger_wait. Do NOT add a per-door hint re-stamp to close
// the gap — one used to live here and it is what overflowed the engine's
// 250-entry triggerstring cache in co-op.
function door_price( base_cost )
{
	c = int( base_cost * door_cost_mult() );
	if ( c < 1 )
		c = 1;
	return c;
}

// THE CROWN ISLAND'S THREE DOORS ARE NEVER PARTY-SCALED (2026-10-04, the first real-run review).
// The 5000 hall gate is the only way out of the crown and BO3 cannot pool points, so in co-op ONE
// player paid it scaled - 6447 duo / 9211 trio / 11974 quad - on about 0.6x a solo player's
// income per round (the round grows ~2.4x for four players, split four ways). Dev money hid it.
// The two 1500 hallway doors follow the same rule (the Power Room is on the same critical path).
// Every tower door keeps door_price. The hint and the charge both read this, so they agree.
function door_price_for( base_cost, flag )
{
	if ( isdefined( flag ) && ( flag == "tod_fall" || flag == "tod_crown_power" || flag == "tod_crown_tele" ) )
		return base_cost;
	return door_price( base_cost );
}

function spawn_buy_trigger( d, pos, cost, slab, flag, dest )
{
	t = spawn( "trigger_radius_use", pos, 0, 96, 100 );
	t TriggerIgnoreTeam();   // REQUIRED for a script-spawned use-trigger
	t SetCursorHint( "HINT_NOICON" );
	// "Open Door to <dest>" EXACTLY — PromptDoors.lua parses the destination out
	// of this hint and puts it in the card TITLE.
	//
	// THAT WAS ONLY TRUE FROM 2026-08-25. This comment previously claimed the
	// card showed "Unlocks: <dest>" and it never did — PromptDoors.lua drew a
	// hardcoded "Locked Area" for all 53 doors, so the Floor 1 door and the
	// Power Room door were byte-identical prompts and the destination the
	// generator carefully authors per door was thrown away. The parse now
	// exists; keep this format EXACT or it silently falls back to the title.
	// The dest + price this trigger's string was minted with, kept so the haven seal can put back
	// EXACTLY this string (haven_seal_watch) - never a re-priced one (the 250-slot rule above).
	t.tod_hint_dest = dest;
	t.tod_hint_price = door_price_for( cost, flag );
	t SetHintString( "Hold ^3[{+activate}]^7 Open Door to " + t.tod_hint_dest + " ^2[Cost: " + t.tod_hint_price + "]" );

	d.tod_trigs[ d.tod_trigs.size ] = t;

	t thread buy_trigger_wait( d, cost, slab, flag );
}

// THE PRICE WATCHER IS GONE (2026-08-30, the 250-triggerstring crash).
//
// THE RULE: SetHintString mints ONE PERMANENT entry in the engine's
// 'triggerstring' BG-cache per DISTINCT string. That cache caps at 250 for the
// WHOLE MATCH and a slot is never freed — not on Delete(), not between rounds.
// Overflow fatals with BG_Cache_GetIndexInternal and BLAMES WHOEVER REGISTERS
// NEXT, so the site named in a crash report is never the accumulator.
//
// WHAT WAS HERE: door_price_watch(), a 2s poll per trigger that re-stamped a
// door's hint whenever door_cost_mult() moved (a join, a drop, a migration),
// gated on a player being within 512u. It was written to BOUND the cost of
// re-stamping and it did — but it could not bound it to zero. `shown` only
// advanced when the re-stamp actually FIRED, so after one party-size change
// every door the party had not yet walked up to still held its load-time price
// and minted a SECOND string on approach. Shipped players hit the cap in
// 4-player games: one party-size change cost ~46 slots, two crossed 250 in the
// upper spiral. The ceiling for this lane alone was 53 x 4 = 212.
//
// WHY DELETING IT IS THE WHOLE FIX, AND WHY THE PRICE STAYS ON SCREEN:
// init() threads door_buy_setup for all 53 doors in one waitless loop, and
// door_buy_setup runs straight through to spawn_buy_trigger — so every hint is
// minted in a SINGLE FRAME off ONE GetPlayers() snapshot. The 53 destinations
// are distinct, so the door-hint set is a fixed 53 whether or not the price is
// in the string. With no watcher that set cannot grow, and stripping the price
// out of the hint would therefore save exactly ZERO slots while making every
// door in the map a blind purchase. It costs nothing to show it, so it is shown.
//
// THE RESIDUAL, ACCEPTED DELIBERATELY: without the watcher a hint can go stale
// if the party size changes mid-match — the sign shows the load-time price
// while buy_trigger_wait charges the live one. A shrinking party is charged
// LESS than shown, a growing party MORE. That is the trade for a hard slot
// bound. If it ever needs closing, close it with IPrintLnBold (chat prints do
// NOT feed this cache) or a clientfield -> LUI lookup. NEVER with another
// SetHintString, and NEVER with a per-door re-stamp — that is this exact bug.

function buy_trigger_wait( d, cost, slab, flag )
{
	level endon( "end_game" );
	for ( ;; )
	{
		self waittill( "trigger", player );

		if ( !isdefined( player ) || !IsPlayer( player ) )
			continue;

		// A REVIVE PRESS IS NOT A PURCHASE — stock door parity
		// (_zm_blockers.gsc:307, and every other stock buy path: _zm_perks.gsc
		// :407, _zm_magicbox.gsc:570, _zm_traps.gsc:318, _zm_unitrigger.gsc:908,
		// whose comment is literally "revive triggers override trap triggers").
		//
		// THIS DOOR LOOP HAD NO PLAYER-STATE GATE AT ALL — no laststand, no
		// is_player_valid, no revive check (audit 2026-08-26; logged once before
		// as ECO-05 in docs/24_full_map_review.md). Two things follow, and BOTH
		// are live in co-op:
		//
		//   1. REVIVING ALSO BOUGHT THE DOOR. Reviving is NOT arbitrated by the
		//      engine's use-prompt selection — stock polls the raw button every
		//      server frame (_zm_laststand.gsc:1129 is_reviving() =
		//      UseButtonPressed() && can_revive()). So holding USE over a downed
		//      teammate satisfied both: the revive proceeded AND this trigger
		//      charged the price. Doorways are the most common down-spot in a
		//      stairwell map, and the two volumes (door 96 radius, revive 75)
		//      overlap constantly.
		//   2. THE CRAWLER HIMSELF COULD BUY IT, with no arbitration needed at
		//      all: a downed player's own revive trigger is
		//      SetInvisibleToPlayer( self ) (_zm_laststand.gsc:853), so THIS was
		//      his only use-ent, and last stand never disables use input.
		//
		// The cost is not just points: the purchase below opens the zone for the
		// rest of the run. That is irreversible, off a button press the player
		// meant as a revive.
		//
		// SILENT on purpose (no deny sound), for the same reason the laststand
		// branches of the crate and station loops are silent: the player is
		// HOLDING use, so a sound here would machine-gun in their ear for the
		// whole crawl.
		//
		// SCOPE — this is a 75-unit-radius / 75-tall bubble centred on the downed
		// player (_zm.gsc:1332 sets the dvar unconditionally; this map overrides
		// nothing), NOT the whole 160-wide landing: a body at the landing edge
		// leaves the door buyable. Flights are 192 apart, so a body one flight
		// down cannot reach either trigger. ACCEPTED COST: a body dropped square
		// in a doorway can pin the party until the bleedout — stock accepts
		// exactly this on every stock door; do not "fix" it with a radius
		// override.
		//
		// ARITY TRAP: in_revive_trigger() is arity 0 and a METHOD on the player;
		// is_player_valid() is arity 3 (all optional) and NOT a method — pass the
		// player as arg 1 and NOTHING else (param 2 is checkIgnoreMeFlag, not
		// ignore_laststand). Always qualify zm_utility:: — shared/ai/zombie_utility
		// ships an identically-shaped is_player_valid in another namespace.
		if ( player zm_utility::in_revive_trigger() )
			continue;
		if ( !( zm_utility::is_player_valid( player ) ) )
			continue;   // downed / spectating (_zm_blockers.gsc:318)

		// THE UPGRADE-PAUSE GUARD — the doors were the ONE map-owned trigger
		// family missing it (map-wide trigger audit 2026-08-28, found twice
		// independently). HOLD-USE IS THE CARD-LOCK BUTTON: during an upgrade
		// event the world is frozen and the player holds USE to lock their
		// pick, so a player frozen within reach of an unbought door bought it
		// too — silently, with no prompt read, at the live price (up to 3000,
		// 7500 for the roof, ~2.4x that in a quad). The zone opened at a moment
		// the player never chose, and the points were gone.
		// SILENT on purpose: the class draft and the upgrade pause both hold
		// USE for seconds at a time, so a deny sound here would machine-gun —
		// the same reasoning as the revive-trigger case just above. The player
		// is not being refused a purchase they attempted; they are being
		// prevented from making one they never attempted.
		if ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( player.tod_menu_frozen ) )
			continue;

		if ( IS_TRUE( d.tod_bought ) )
			return;
		// THE SEALED WAY DOWN (2026-10-04, haven_seal_watch): a haven floor's way down refuses
		// until that floor's haven is taken. Asked of the haven itself on every press (the
		// watch's prompt can lag it by half a second); the refusal sound is throttled per player
		// because a held USE re-fires the trigger.
		if ( isdefined( level.tod_haven_door_seal_fn ) && [[ level.tod_haven_door_seal_fn ]]( flag ) == 1 )
		{
			if ( !isdefined( player.tod_seal_deny_ms ) || GetTime() - player.tod_seal_deny_ms > 1500 )
			{
				player.tod_seal_deny_ms = GetTime();
				player PlaySound( "zmb_no_purchase" );
				seal_log( "REFUSED flag=" + flag + " player=" + player.name + " round=" + level.round_number );
			}
			continue;
		}
		// LIVE price, re-read on every attempt — `cost` is the AUTHORED base.
		price = door_price_for( cost, flag );   // the crown island's doors are flat (door_price_for)
		if ( !( player zm_score::can_player_purchase( price ) ) )
		{
			player PlaySound( "zmb_no_purchase" );
			continue;
		}

		player zm_score::minus_to_player_score( price );
		player PlaySound( "zmb_cha_ching" );
		d.tod_bought = true;
		tod_luck::door_buy( player );   // LUCK +8 to the buyer (v5 luck bar)

		if ( flag != "" && level flag::exists( flag ) )
		{
			level flag::set( flag );   // activates the zone adjacency
		}

		if ( isdefined( slab ) )
			level thread open_slab( d, slab );   // v16.11: slides, then the old Hide/NotSolid/ConnectPaths

		// retire BOTH triggers (clear the prompt on the now-open door)
		for ( i = 0; i < d.tod_trigs.size; i++ )
		{
			if ( isdefined( d.tod_trigs[ i ] ) )
			{
				d.tod_trigs[ i ] SetHintString( "" );
				d.tod_trigs[ i ] TriggerEnable( false );
			}
		}
		return;
	}
}

// ---------------------------------------------------------------------------
// v16.11 — the one open path every door takes (see the TOD_DOOR_SLIDE header).
// Threaded by its callers so the slide never delays the trigger retire
// or the flag set. Falls through to the instant open for non-lap doors, for
// a door door_buy_setup never stamped (dev path before init), or with the
// define off.
// ---------------------------------------------------------------------------
function open_slab( d, slab )
{
	if ( !isdefined( slab ) )
		return;
	if ( TOD_DOOR_SLIDE && isdefined( d ) && IS_TRUE( d.tod_is_lap ) && isdefined( d.tod_slide_dx ) )
	{
		if ( isdefined( d.tod_org ) )
		{
			tod_perk_scatter::derez_burst( d.tod_org );
			tod_perk_scatter::play_sound_at_origin( d.tod_org, TOD_DOOR_SLIDE_SOUND, 4 );
		}
		slab MoveX( d.tod_slide_dx, TOD_DOOR_SLIDE_SECS );
		slab waittill( "movedone" );
		if ( !isdefined( slab ) )
			return;
	}
	slab Hide();
	slab NotSolid();
	slab ConnectPaths();
}

// ---------------------------------------------------------------------------
// v13.9 — PUBLIC: open a door by its script_flag WITHOUT a purchase.
//
// Born from a live report (user 2026-08-29): "when i took the teleporter I
// ended up in teleporter room with door closed which is what I expected but
// then I went to 1 health and hear the teddy bear like I was out of bounds".
// That IS the out-of-bounds punisher: a zone only activates when its door's
// flag sets, so a player teleported into the sealed bay stood in an INACTIVE
// zone and stock's playable-area monitor drained them to 1 with the giggle.
// Exempting arrivals from the monitor instead would have minted an
// invulnerable camp room (inactive zone = no spawns, sealed slab = no path),
// so the fix follows the user's own teleporter rule to its conclusion:
// ARRIVING BY TELEPORTER OPENS THE BAY FROM THE INSIDE, free — flag set (zone
// live, monitor satisfied, risers wake), slab open (zombies path in — no
// stranded actors), prompts retired. Mirrors the buy path exactly, minus the
// charge and the luck. Idempotent; returns true if the door is open after.
function force_open_by_flag( flag )
{
	// A collapsed gate has no buy/slab entity, but teleport/dev callers still
	// need its existing zone flag. It must never become an inactive safe floor.
	drop = tod_door_data::get_drop_by_flag( flag );
	if ( isdefined( drop ) ) return broken_open( drop );
	if ( !isdefined( level.tod_doors_by_flag ) || !isdefined( level.tod_doors_by_flag[ flag ] ) )
		return false;
	d = level.tod_doors_by_flag[ flag ];
	if ( IS_TRUE( d.tod_bought ) )
		return true;
	d.tod_bought = true;

	if ( isdefined( d.tod_flag ) && d.tod_flag != "" && level flag::exists( d.tod_flag ) )
	{
		level flag::set( d.tod_flag );
	}
	if ( isdefined( d.tod_slab ) )
		level thread open_slab( d, d.tod_slab );   // v16.11: same slide as a purchase
	for ( i = 0; i < d.tod_trigs.size; i++ )
	{
		if ( isdefined( d.tod_trigs[ i ] ) )
		{
			d.tod_trigs[ i ] SetHintString( "" );
			d.tod_trigs[ i ] TriggerEnable( false );
		}
	}
	return true;
}

// ---------------------------------------------------------------------------
// ENEMY UNLOCKS — the tower gets harder the higher you climb
// ---------------------------------------------------------------------------
// User 2026-08-21: "Every time you open a door to a breather (the gold section
// on the tower bar) we introduce a new type of enemy. First will be the
// protector — they won't spawn until that door is opened. They start coming on
// the round it's opened, then every 3 rounds in waves."
//
// The gate is the ROUND STAMP, not just a bool: _tod_bosses::protector_due
// anchors its every-3-rounds cadence to the round the door was bought, so the
// wave lands on that round and then every third one after — never on the old
// global round-3 grid.
//
// Breather laps are 10/20/30/40 (gen_tower_map.js BREATHER_LAPS). Slots 2-4
// are reserved for future enemy types; only the protector is wired today, so
// opening those doors currently unlocks nothing (no dead references).
// docs/160 — THE DESCENT re-keys the ladder to the doors as they are MET
// going down. enter_lapN sits at the BOTTOM of lap N (the landing where lap
// N-1 ends), so the door that lets a descending party INTO breather lap B is
// enter_lap(B+1). The ladder keeps its difficulty order — protector first,
// then reaver, sprinter, hellhound — so the first lounge passed (40) unlocks
// the easiest elite and the last (10) the hounds. LOCKSTEP with DESCENT in
// gen_tower_map.js; with 0 the climb keys below are live.
#define TOD_DOORS_DESCENT  1

function broken_routes_init()
{
	if ( !isdefined( level.player_damage_callbacks ) ) level.player_damage_callbacks = [];
	ArrayInsert( level.player_damage_callbacks, &broken_fall_guard, 0 );
	upper = GetEntArray( "tod_tower_drop_upper", "targetname" );
	lower = GetEntArray( "tod_tower_drop_lower", "targetname" );
	for ( i = 0; i < upper.size; i++ ) upper[ i ] thread broken_touch( true );
	for ( i = 0; i < lower.size; i++ ) lower[ i ] thread broken_touch( false );
	broken_log( "INIT rev=1 upper=" + upper.size + " lower=" + lower.size + " fixed_layout=1" );
}

function broken_open( row )
{
	if ( !level flag::exists( row.flag ) )
	{
		broken_log( "NO_ZONE_FLAG lap=" + row.lap + " flag=" + row.flag );
		return false;
	}
	if ( !level flag::get( row.flag ) )
	{
		level flag::set( row.flag );
		broken_log( "ZONE_OPEN lap=" + row.lap + " flag=" + row.flag + " cost=0" );
	}
	return true;
}

function broken_touch( upper )
{
	level endon( "end_game" );
	self endon( "death" );
	row = tod_door_data::get_drop_info( int( self.script_int ) );
	if ( !isdefined( row ) )
	{
		broken_log( "MISSING_ROUTE trigger=" + self GetEntityNumber() );
		return;
	}
	while ( true )
	{
		self waittill( "trigger", player );
		if ( !isdefined( player ) || !IsPlayer( player ) || !IsAlive( player ) ) continue;
		broken_open( row );
		if ( upper )
		{
			if ( !isdefined( player.tod_drop_lap ) || player.tod_drop_lap != row.lap || !isdefined( player.tod_drop_touch_ms ) || GetTime() - player.tod_drop_touch_ms > 1500 )
			{
				player.tod_drop_land_lap = -1;
				broken_log( "APPROACH player=" + player GetEntityNumber() + " lap=" + row.lap + " origin=" + player.origin + " landing=" + row.lower );
			}
			player.tod_drop_lap = row.lap;
			player.tod_drop_ms = GetTime();
			player.tod_drop_touch_ms = GetTime();
		}
		else if ( !isdefined( player.tod_drop_land_lap ) || player.tod_drop_land_lap != row.lap )
		{
			player.tod_drop_land_lap = row.lap;
			player.tod_drop_land_ms = GetTime();
			broken_log( "LANDING_VOLUME player=" + player GetEntityNumber() + " lap=" + row.lap + " origin=" + player.origin + " health=" + player.health );
		}
		wait 0.1;
	}
}

function broken_fall_guard( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, psOffsetTime )
{
	if ( sMeansOfDeath != "MOD_FALLING" || !isdefined( self.tod_drop_lap ) || !isdefined( self.tod_drop_ms ) ) return -1;
	if ( GetTime() - self.tod_drop_ms > 2500 ) return -1;
	row = tod_door_data::get_drop_info( self.tod_drop_lap );
	if ( !isdefined( row ) ) return -1;
	o = self.origin;
	if ( o[0] < row.lo[0] || o[0] > row.hi[0] || o[1] < row.lo[1] || o[1] > row.hi[1] || o[2] < row.lo[2] - 8 || o[2] > row.lo[2] + 24 ) return -1;
	broken_log( "LANDING_PROTECTED player=" + self GetEntityNumber() + " lap=" + row.lap + " damage=" + iDamage + " origin=" + o );
	self.tod_drop_ms = -10000;
	return 0;
}

function broken_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_DROP] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// ===========================================================================
// DEV ONLY — open every door as if it had been bought.
// Called from _tod_main::dev_crown_test (gated on level.tod_dev). Ship builds
// never reach it.
//
// WHY THIS EXISTS RATHER THAN JUST SETTING THE FLAGS. The dev harness first
// tried `level flag::set( "enter_lapN" )` for all 53 and called that "the same
// as buying every door". It is not. A real purchase (see the buy loop above)
// does THREE things, and the flag is only the first (a fourth, breather_unlock,
// armed the Map One elite directors per lounge door; it retired whole with them
// 2026-10-05):
//     level flag::set( flag )      - activates the zone adjacency
//     slab Hide/NotSolid/ConnectPaths - the barrier and its NAV CUT. Flags
//                                    alone leave 53 solid slabs standing and
//                                    the navmesh severed, so the horde cannot
//                                    path the tower even though the zones are
//                                    "open".
//     the two buy triggers retire  - or every opened doorway still prompts.
// Doing only the first is why a dev session looked open but played sealed.
// ===========================================================================
function dev_open_all_doors()
{
    doors = GetEntArray( "zombie_door", "targetname" );
    for ( i = 0; i < doors.size; i++ )
    {
        d = doors[ i ];
        if ( !isdefined( d ) )
            continue;

        // THE FALL'S GATE IS NEVER A DEV DOOR (user 2026-09-25, twice: "the
        // crown door needs to be closed ... you need to buy the door. It's still
        // open. So we can't miss this again"). tod_dev implies this harness, and
        // it opened the 5000 hall gate at spawn in every dev build — the alarm ->
        // points -> buy the gate loop IS the run's opening, so the gate stays
        // shut and priced even in a dev session. _tod_fall publishes the flag.
        if ( isdefined( level.tod_fall_gate_flag ) && isdefined( d.script_flag ) && d.script_flag == level.tod_fall_gate_flag )
        {
            skip_line = "[TOD_FALL] DEV door harness SKIPS the Fall gate (" + d.script_flag + ") - it stays a 5000 buy";
            /#
            PrintLn( skip_line );
            #/
            continue;
        }

        if ( isdefined( d.script_flag ) && d.script_flag != "" && level flag::exists( d.script_flag ) )
        {
            level flag::set( d.script_flag );
        }

        if ( isdefined( d.target ) )
        {
            slab = GetEnt( d.target, "targetname" );
            if ( isdefined( slab ) )
                level thread open_slab( d, slab );   // v16.11: slides if door_buy_setup stamped this ent, else the instant open
        }

        d.tod_bought = true;
        if ( isdefined( d.tod_trigs ) )
        {
            for ( t = 0; t < d.tod_trigs.size; t++ )
            {
                if ( isdefined( d.tod_trigs[ t ] ) )
                {
                    d.tod_trigs[ t ] SetHintString( "" );
                    d.tod_trigs[ t ] TriggerEnable( false );
                }
            }
        }
    }
}
