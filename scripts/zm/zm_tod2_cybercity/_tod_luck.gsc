// =============================================================================
// _tod_luck.gsc — THE LUCK BAR (user 2026-08-20): per-player 0..100%, shown
// bottom-left, SPENT on upgrade rolls (higher bar = better rarity odds),
// FULL RESET to 0 after each upgrade event (user decision).
//
// THE OVERCHARGE (v14.9: a secret 100..150 band with a zap animation and a
// both-ULTIMATE deal) WAS RETIRED 2026-09-28 (docs/187). The bar tops out at 100.
//
// SOURCES (LAST HIT TAKES ALL — user: "Last hit will get all points for
// luck. Whether thats a zombie protector or panzer"):
//   zombie kill      +normalized (see below); headshot kills x1.5
//   an elite         +4  (the killer: Mangler, Doppelghast, the Dealer; the
//                         Panzer's +20 and the other Map One rows retired
//                         whole 2026-10-05)
//   revive           +15 (the reviver)
//   door purchase    +8  (the buyer — _tod_doors calls in)
//   going down       -25
//
// THE BALANCE CORE (solo/duo/trio/quad fairness as rounds scale): raw
// per-kill luck would explode with round size and starve co-op players
// (zombies split p ways). Instead each round computes
//     luck_per_kill = KILL_BUDGET * players / round_zombie_total
// so a player killing their FAIR SHARE of any round earns ~KILL_BUDGET
// regardless of round number or lobby size: solo clears the whole round =
// +KILL_BUDGET; in a quad the round is ~bigger but split 4 ways — each fair
// share still = +KILL_BUDGET. Round size comes from the stock spawn-budget formula
// (zm::get_zombie_count_for_round, _zm.gsc:3842 - the same number the endless
// flow spends). More zombies per round -> less luck per kill, automatically.
//
// The permanent LUCK upgrade domain = +10% GAIN RATE per level (user pick):
// every gain is multiplied by (1 + 0.10 * luck_level). Losses are not.
//
// HUD: all-LUI (v6 — the server hudelem bar never sat cleanly in the frame
// art's window). Every bar change pushes tod_upgrade_ui::set_luck_pct, which
// drives the EXISTING todUpgLuck clientfield (bar/10, 0..10) — zero new
// clientuimodel bits (pool is at its 61-bit ceiling); tod_upgrade.lua swaps
// between 11 baked bar images (i_tod_luck_00..10, one per level).
//
// Public API:
//   add( player, amount )      — luck gain (gain-rate mult applies)
//   drain( player, amount )    — luck loss (no mult)
//   get( player )              — current 0..150 (>100 = the secret band)
//   spend( player )            — zero the bar + refresh HUD (post-upgrade)
//   on_zombie_kill( attacker, b_headshot ) — the normalized kill award
//   THE HOT STREAK (docs/201 section 5): heat( player ), heat_mult( player ),
//   streak_result( player, best, source, fb_secs ) (also level.tod_luck_streak_fn),
//   streak_end( player, why ); the table level.tod_heat_mult
//
// DEV LOGS (2026-09-29, with level.tod_dev; the balance record for the 12% kill budget):
//   [TOD_LUCK] RATE  — every round change: the round's zombie total and the per-kill value
//   [TOD_LUCK] BAR   — every round change: each player's bar (how fast it fills per round)
//   [TOD_LUCK] SPENT — the bar dropped to 0 without a down: its level just before (a card
//                      deal / altar / Black Market spin zeroes it); deal=1 = a world pause
//                      was up (a card deal); the spin also logs [TOD_SHOP] SPIN_BUY luck=
//   [TOD_LUCK] BARS  — a reward worth N bars landed (add_bars): who, N, the bar after it
//   [TOD_LUCK] STREAK — every hot-streak change (docs/201): who, the pull (deal / spin / down), its best rarity,
//                      the streak, heat old -> new and the odds multiplier now in force
// =============================================================================

#using scripts\shared\callbacks_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm;           // get_zombie_count_for_round (the spawn budget)
#using scripts\zm\_zm_spawner;

#insert scripts\shared\shared.gsh;

#using scripts\zm\zm_tod2_cybercity\_tod_upgrades;
#using scripts\zm\zm_tod2_cybercity\_tod_upgrade_ui;   // set_luck_pct (no cycle: upgrade_ui imports only shared)
#using scripts\zm\zm_tod2_cybercity\_tod_killconfirm;  // v18.96: elite_kill (the red crosshair snap) + ding (one owner; imports only shared, no cycle)

// THE HOT STREAK's HUD channel (docs/201 section 5): a LuiNotifyEvent name must be a
// precached eventstring or the event silently never fires.
#precache( "eventstring", "tod_luck_heat" );

#define TOD_LUCK_MAX           100
// v14.9 OVERCHARGE CEILING (user 2026-08-30): the bar secretly tracks past 100
// up to here. Everything VISIBLE still keys off TOD_LUCK_MAX (the HUD's 10
// segments, the pips); this is the true clamp in set_bar, the odds keep riding
// the raw value in roll_rarity, and AT this value the overcharge state fires
// (animation + zap SFX + both-ULTIMATE deal). LOCKSTEP PAIR with
// TOD_UPG_GUAR_BOTH_BAR in _tod_upgrades.gsc and with
// TOD_UPG_LUCK_OVERMAX_PCT in _tod_upgrade_ui.gsc — all three must move
// together (defines are per-file; the modules cannot share one).
// 2026-09-28 (docs/187, user: "I dont want overcharge anymore"): THE OVERCHARGE IS RETIRED.
// The secret 100..150 band, its zap animation/sound and the both-ultimate deal are gone;
// the bar's true clamp is its visible top again.
#define TOD_LUCK_OVERMAX       TOD_LUCK_MAX
// THE KILL BUDGET: a fair-share round clear ~= this much luck. 40 -> 18 on 2026-08-20
// (user: "way too easy, basically maxed every time"); 18 -> 12 on 2026-09-29 (user: "Make
// it 12%"). The second cut makes room for SKILL: at 18 a busy player reached ~72% from
// kills alone by each 4-round card deal (plus 10 a door), so a full bar was nearly
// automatic and any new luck source overflowed the cap. At 12 kills alone bring ~48%,
// and the skill sources being designed (the Lucky Die, 2026-09-29) decide the rest.
// SIDE EFFECT, recorded for the next tune: a DOWN (15) and a DOOR (10) are now each
// worth about a whole round of kill luck.
#define TOD_LUCK_KILL_BUDGET   12
// [v17.1] THE LATE-ROUND KILL BOOST (user 2026-09-03: *"specifically on zombie
// kills we need a slight buff later rounds ... 4% extra after round 15"*, with
// a worked table: r16 104%, r17 108%, r18 112%).
//
// WHY THE NORMALIZATION ALONE WAS NOT ENOUGH. per_round_rate() divides the
// budget by the round's zombie count, which is EXACTLY right if you clear the
// round — a full clear always pays TOD_LUCK_KILL_BUDGET whatever the round
// number. Late game you cannot clear: stock's count grows with the SQUARE of
// the round past 10 (get_zombie_count_for_round, _zm.gsc:3853), the endless
// twist starts the next round on the last SPAWN rather than the last kill, so
// the horde outruns you and you take a shrinking SHARE of a per-kill value that
// is itself shrinking quadratically. Two other late-game losses compound it:
// door income (TOD_LUCK_DOOR, 10 a door) stops entirely once the tower is
// bought, and a DOWN used to cost 25 against a round's fair share of 18 — cut
// to 15 the same day (see the define) for exactly that reason.
//
// LINEAR, NOT COMPOUNDING — and the difference matters enormously here. The
// user's own table (104 / 108 / 112) is linear, which is the safe reading:
//   linear      r20 1.20   r30 1.60   r40 2.00   r50 2.40   r100 4.40
//   compounding r20 1.22   r30 1.80   r40 2.67   r50 3.95   r100 27.6  <-- no
// They are near-identical for the first few rounds and diverge violently by
// round 50, so "4% a round" has to be written down as which one it is.
//
// WHERE IT SATURATES, so nobody is surprised later: a fair-share full clear
// pays KILL_BUDGET x mult (12 x mult since 2026-09-29), so it reaches the 100
// bar cap around round 198 (round 130 at the old 18) — far past
// a normal run. Deliberately NOT capped: an artificial ceiling nobody asked for is
// the kind of silent divergence that gets rediscovered as a bug, and the bar
// cap already bounds the outcome.
#define TOD_LUCK_LATE_FROM     15     // rounds ABOVE this get the boost
#define TOD_LUCK_LATE_PER_RND   0.04  // +4% of the base rate per round past it
#define TOD_LUCK_HEADSHOT_MULT 1.5
// every elite's last hit (the killer). Was TOD_LUCK_PROTECTOR, the catch-all the
// Mangler / Doppelghast / Dealer already rode; the Panzer (20), Reaver (6),
// hellhound (3), sprinter (4) and Keeper (20) rows retired whole 2026-10-05.
#define TOD_LUCK_ELITE         4
#define TOD_LUCK_REVIVE        15
// DOOR BUY = A FLAT 10% OF THE BAR (user 2026-08-27: "lets make buying a door
// 10% luck increase"). History: 8 -> 5 (2026-08-20 nerf) -> 8.75 (2026-08-21,
// "opening a door gives luck, 1.75x it") -> 10 now, which is also the first time
// this number is a round share of the bar rather than the product of two
// tunings: ten doors is exactly a full bar, and one door lights exactly one of
// the HUD's ten segments. BUYER ONLY — _tod_doors passes the purchasing player,
// so it does not pay the whole party.
//
// The LUCK domain still multiplies it (+10% gain rate/Lv), so a maxed LUCK
// player banks 15 per door and reaches the ULTIMATE guarantee in seven.
#define TOD_LUCK_DOOR          10
// DUPLICATE-DROP CONSOLATION (user 2026-08-30: "if a player already has a
// pap gun but gets a pap drop they will get 20% luck. And if they get a perk
// bottle with max perks they will get 10% luck"). Paid by _tod_powerups via
// level.tod_luck_dupe_fn (set in init below — powerups cannot #using this
// module: powerups -> luck -> upgrades -> powerups is the cycle the KB
// forbids). Routed through add(), so the LUCK domain's gain rate multiplies
// these like every other source, and the segment pips fire.
#define TOD_LUCK_PAP_DUPE      20     // PaP drop, everything already packed
#define TOD_LUCK_PERK_DUPE     10     // perk bottle, every sellable perk owned
// A DOWN COSTS 15 (user 2026-09-03: "Going down can be -15%"). Was 25, which
// was set when a round's fair share was 40 — after the 2026-08-20 cut to 18 a
// single down cost MORE THAN A WHOLE ROUND OF KILLS, so late game one bad
// round could outweigh two good ones. 15 also lands it exactly on
// TOD_LUCK_REVIVE, so a teammate picking you up now returns to the party
// precisely what the down took from you.
#define TOD_LUCK_DOWN          15     // lost on going down
#define TOD_LUCK_GAIN_PER_LVL  0.10   // RECORD: the LUCK domain was +10% gain rate / Lv (5 levels)
#define TOD_LUCK_GAIN_MAX      1.00   // LUCK at Lv9 (user 2026-09-28: "Max both at +100% at level 9"), x tod_upgrades::card_curve

// RAMPAGE — A DOWN IS A PARTY EVENT (v14.36, user 2026-08-30: "On rampage if a
// player goes down everyone loses 50% luck"). The SIXTH rampage lever, and the
// first one that is not about the enemy at all: it attacks the party's shared
// card economy instead of the horde's stat block.
//
// MULTIPLICATIVE, not a flat subtraction — "loses 50%" reads as HALVE THE BAR,
// and halving is the version that scales: it costs a banked player 50 and a
// broke player almost nothing, so the punishment tracks how much you had to
// lose. That also makes it bite hardest at exactly the moment the party cares
// most — a full bar or an OVERCHARGE at 150 drops to 75 and falls out of the
// guaranteed-ultimate band, which is the loudest possible consequence and
// needs no new cue to be felt.
//
// APPLIES TO EVERY PLAYER INCLUDING THE ONE WHO WENT DOWN, and it is ON TOP OF
// that player's existing TOD_LUCK_DOWN (15 since 2026-09-03). Deliberate, and the alternative was
// considered: making the halving REPLACE the 25 would mean a low-bar player
// under RAMPAGE loses LESS than the same player in a normal match (bar 10:
// halve = -5, versus the flat -25 that floors them). A hard mode must never be
// softer than the base game on any input, so the base penalty stays untouched
// and this stacks on top. Net effect at a full bar: the downed player pays
// 62.5, everyone else pays 50.
#define TOD_LUCK_DOWN_PARTY_MULT 0.5
// v16.59 REVERTED (user 2026-09-02: "we need to revert the losing luck when
// player goes down on rampage"). The v14.38 party halving is OFF: a down under
// RAMPAGE now costs the downed player the ordinary TOD_LUCK_DOWN 15 and nobody
// else anything — identical to a normal match. party_down_drain() and its
// contract comment stay so the lever is one flip away; the switch below is the
// only gate on the call in down_watcher.
#define TOD_LUCK_RAMPAGE_PARTY_DRAIN 0   // 1 = v14.38 rule (a RAMPAGE down halves EVERY bar); 0 = off (v16.59)

// --- THE AUDIBLE LUCK LADDER (2026-08-29, docs/43 items 1-2) ----------------
// The bar drove everything in this map and made no sound from round 1 to the
// finale. Two cues, deliberately paired:
//   * tod_headshot_ding  — headshot KILL, the shooter only. Map 1's Apex ding
//     (acc\fx\headshot_ding.wav), the user's explicit pick.
//   * tod_luck_pip01..10 — one per HUD segment that lights, a major scale
//     climbing 16 semitones so "nearly full" is audible without looking.
// They compound on purpose: a headshot kill pays 1.5x luck, so the shot that
// dings is the shot most likely to light a segment a beat later.
#define TOD_LUCK_SEGS          10     // must match the HUD's segment count
#define TOD_LUCK_PIP_DELAY     0.12   // pip lands just AFTER the ding, never on top of it
// THE LUCKY SOURCES (2026-09-29: the Lucky Clover drop, the Golden Zombie): a reward "worth
// N bars" lands as N one-segment steps this far apart, so the player watches N segments
// light one after another and hears the pip ladder climb N rungs (add_bars below).
#define TOD_LUCK_BAR_STEP_SECS 0.22

// --- THE HOT STREAK (docs/201 section 5, user 2026-10-02: "the hot hand effect as well ... Not crazy but a bit
// too allow for those crazy lucky games") ------------------------------------------------------------------
// A STREAK of PULLS (a card deal or a Black Market spin) that came up EPIC or better. An EPIC adds
// TOD_STREAK_EPIC, a LEGENDARY TOD_STREAK_LEGENDARY; anything less ENDS it, and so does going down. HEAT is the
// streak minus one, at most TOD_STREAK_HEAT_MAX: 1 WARM, 2 HEATING UP, 3 ON FIRE (NBA Jam's two-in-a-row /
// three-in-a-row). Heat multiplies the EPIC and LEGENDARY odds of every card and spin by level.tod_heat_mult
// (COMMON pays); the luck bar's guarantees never read it. It only ever helps: a miss ends it, never worse odds.
// THE NUMBERS ARE ONE TABLE, set in init() below and read by _tod_upgrades roll_rarity (as a field: it cannot
// #using this module) and _tod_shop roll_rarity (heat_mult) - LOCKSTEP with TodSpinReel.lua HEAT_MULT, which
// draws the spin's true odds. tools/test_hot_streak.js gates all of it.
// REJECTED (recorded so nobody brings it back): "+1 heat per Epic, -1 per miss". Simulated
// (tools/near_miss/sim_hot_streak.js) players were hot on 55% of pulls and ON FIRE in 87% of runs, because
// Epics are common (two cards a deal plus the guarantees): heat became the normal state. A streak must END on a miss.
#define TOD_STREAK_EPIC        1
#define TOD_STREAK_LEGENDARY   2
#define TOD_STREAK_HEAT_MAX    3
#define TOD_STREAK_RESEND_SECS 5      // the HUD's copy is re-sent this often while hot (a HUD rebuilt on respawn starts empty)


#namespace tod_luck;

function init()
{
	level thread per_round_rate();
	callback::on_spawned( &on_player_spawned );
	zm_spawner::register_zombie_death_event_callback( &on_zombie_death );

	// The duplicate-drop consolation lane for _tod_powerups (see the
	// TOD_LUCK_*_DUPE defines — the pointer exists because a #using from
	// powerups would close an import cycle).
	level.tod_luck_dupe_fn = &dupe_award;

	// THE HOT STREAK (docs/201 section 5): the one multiplier table (cold, WARM, HEATING UP, ON FIRE) and the
	// lane the card deal reports through (_tod_upgrade_ui cannot #using this module: the same cycle as above).
	level.tod_heat_mult = array( 1.0, 1.15, 1.30, 1.50 );
	level.tod_luck_streak_fn = &streak_result;
}

// PUBLIC via level.tod_luck_dupe_fn. kind: "pap" (drop grabbed with every
// packable gun already packed, +20) or "perk" (bottle grabbed with every
// sellable perk owned, +10). Values live HERE like every luck number.
function dupe_award( player, kind )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return;
	n = TOD_LUCK_PERK_DUPE;
	if ( isdefined( kind ) && kind == "pap" )
		n = TOD_LUCK_PAP_DUPE;
	add( player, n );
}

// ---------------------------------------------------------------------------
// The per-round kill rate — recomputed at every round boundary.
// ---------------------------------------------------------------------------

function per_round_rate()
{
	level endon( "end_game" );

	level.tod_luck_per_kill = 1.0;
	last = 0;
	for ( ;; )
	{
		r = level.round_number;
		if ( isdefined( r ) && r != last )
		{
			last = r;
			p = GetPlayers().size;
			if ( p < 1 )
				p = 1;
			total = zm::get_zombie_count_for_round( r, p );
			if ( !isdefined( total ) || total < 1 )
				total = 24;
			// [tod 2026-09-09] PUBLISHED for anyone else normalising by round
			// size -- the Necromancer's Soul Bomb (_tod_necro_summon::bomb_souls_need)
			// is the second customer. One writer,
			// one stock call, no second per-round watcher: this loop already
			// runs and already has the number.
			level.tod_round_zombie_total = total;
			base = TOD_LUCK_KILL_BUDGET * p / total;
			// [v17.1] late-round boost — linear, see the defines
			if ( r > TOD_LUCK_LATE_FROM )
				base = base * ( 1.0 + TOD_LUCK_LATE_PER_RND * ( r - TOD_LUCK_LATE_FROM ) );
			level.tod_luck_per_kill = base;

			dev_log( "RATE round=" + r + " players=" + p + " zombies=" + total + " per_kill=" + base + " budget=" + TOD_LUCK_KILL_BUDGET );
			foreach ( pl in GetPlayers() )
			{
				if ( !isdefined( pl ) || !isplayer( pl ) )
					continue;
				b = 0;
				if ( isdefined( pl.tod_luck_bar ) )
					b = int( pl.tod_luck_bar );
				dev_log( "BAR round=" + r + " player=" + pl GetEntityNumber() + " bar=" + b );
			}
		}
		wait 1;
	}
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

function add( player, amount )
{
	if ( !isdefined( player ) || !isplayer( player ) || !isdefined( amount ) )
		return;
	// LUCK domain: gain-rate boost (user pick — gains only, never losses)
	lvl = tod_upgrades::get_level( player, "luck" );
	gain = TOD_LUCK_GAIN_MAX * tod_upgrades::card_curve( lvl );   // 2026-09-28 (user): 9 levels, log, +100% at Lv9 (+30 / 48 / 60 / 70 / 78 / 85 / 90 / 95 / 100%)
	// LUCK has NO dark step since 2026-09-05 (user: "Remove dark luck"); the
	// v17.10 x2.00 lane (+0.50 gain) was retired here and in set_no_dark().
	if ( gain > 0 )
		amount = amount * ( 1.0 + gain );

	set_bar( player, bar_of( player ) + amount );
}

// A reward worth N BARS (N HUD segments, 10 luck each), paid as N separate steps
// TOD_LUCK_BAR_STEP_SECS apart: every step is its own add(), so the LUCK card multiplies
// each one like every other gain, and set_bar pips once per segment actually crossed (a
// full bar stays silent, so a capped reward never sings for nothing). WAITS: callers
// thread it. First users: _tod_lucky (the Lucky Clover grab, the Golden Zombie's killer).
function add_bars( player, n )
{
	if ( !isdefined( player ) || !isplayer( player ) || !isdefined( n ) || n < 1 )
		return;
	player endon( "disconnect" );
	level endon( "end_game" );
	for ( i = 0; i < n; i++ )
	{
		if ( i > 0 )
			wait TOD_LUCK_BAR_STEP_SECS;
		add( player, TOD_LUCK_MAX / TOD_LUCK_SEGS );
	}
	dev_log( "BARS player=" + player GetEntityNumber() + " n=" + n + " bar=" + int( bar_of( player ) ) );
}

function drain( player, amount )
{
	if ( !isdefined( player ) || !isplayer( player ) || !isdefined( amount ) )
		return;
	set_bar( player, bar_of( player ) - amount );
}

function get( player )
{
	return int( bar_of( player ) );
}

// RAMPAGE ONLY — one player going down HALVES EVERY player's bar (v14.36).
// Called from down_watcher on the laststand EDGE, so it fires once per down.
//
// ONE READER of level.tod_rampage_on in this file, right here. _tod_rampage.gsc
// is the sole WRITER and nothing is imported in either direction — the same
// field-read contract _tod_zombie_speed::full_round uses. With the field absent
// or false this function is never called at all, so RAMPAGE-off behaviour is
// byte-identical to before.
//
// EVERY WRITE GOES THROUGH set_bar, deliberately, because set_bar is the single
// owner of four things this must not re-implement: the 0/150 clamp, the HUD
// refresh, the segment-pip rule (downward crossings are silent, so a halving
// makes no ding — correct, the bar dropping IS the read), and the OVERCHARGE
// state. That last one matters most: overcharge_driver polls its own exit, so
// halving a 150 bar to 75 ends the zap animation and its 3s deep-zap within one
// 0.15s tick with nothing to clean up here.
//
// GetPlayers() is the whole connected party, which is what "everyone" means.
// Players who are themselves down, or dead and spectating, are included on
// purpose — a bar is a bar, and skipping them would hand a wiped-out teammate
// an untouched bar to walk back in with. In SOLO "everyone" is one player, so
// the lever still bites: a solo down costs 62.5 of a full bar instead of 25.
//
// NO DEBOUNCE, per the spec: two players going down inside the same 0.5s
// down_watcher tick fire this twice and the bar quarters. That is two downs and
// two penalties, and it is the correct reading of "if a player goes down" — but
// it IS the sharpest edge in the feature, so it is the first knob to revisit if
// co-op wipes feel unrecoverable.
function party_down_drain()
{
	foreach ( p in GetPlayers() )
	{
		if ( !isdefined( p ) || !isplayer( p ) )
			continue;
		set_bar( p, bar_of( p ) * TOD_LUCK_DOWN_PARTY_MULT );
	}
}

// The upgrade event consumed the bar (user: full reset to 0).
function spend( player )
{
	set_bar( player, 0 );
}

// ---------------------------------------------------------------------------
// THE HOT STREAK (docs/201 section 5; the rule and the numbers are at the defines)
// ---------------------------------------------------------------------------

// PUBLIC: this player's heat, 0 cold .. TOD_STREAK_HEAT_MAX.
function heat( player )
{
	if ( !isdefined( player ) || !isdefined( player.tod_luck_heat ) )
		return 0;
	return player.tod_luck_heat;
}

// PUBLIC: the multiplier heat puts on the EPIC and LEGENDARY slices of a roll (1.0 when cold). _tod_shop
// roll_rarity calls it; _tod_upgrades roll_rarity reads the same level.tod_heat_mult table itself.
function heat_mult( player )
{
	if ( !isdefined( level.tod_heat_mult ) )
		return 1.0;
	h = heat( player );
	if ( h < 0 )
		h = 0;
	if ( h > level.tod_heat_mult.size - 1 )
		h = level.tod_heat_mult.size - 1;
	return level.tod_heat_mult[ h ];
}

// PUBLIC (and level.tod_luck_streak_fn): one PULL's result. best = the best rarity it SHOWED, on the card scale
// 1 COMMON .. 4 LEGENDARY (below 1 = nothing countable: the streak is left alone). EPIC and LEGENDARY build the
// streak, anything less ends it. fb_secs: how long the sound waits, so it lands after the pull's own moment.
function streak_result( player, best, source, fb_secs )
{
	if ( !isdefined( player ) || !isplayer( player ) || !isdefined( best ) || best < 1 )
		return;
	s = 0;
	if ( isdefined( player.tod_luck_streak ) )
		s = player.tod_luck_streak;
	old = heat( player );
	if ( best >= 4 )
		s = s + TOD_STREAK_LEGENDARY;
	else if ( best >= 3 )
		s = s + TOD_STREAK_EPIC;
	else
		s = 0;
	h = s - 1;
	if ( h < 0 )
		h = 0;
	if ( h > TOD_STREAK_HEAT_MAX )
		h = TOD_STREAK_HEAT_MAX;
	player.tod_luck_streak = s;
	player.tod_luck_heat = h;
	change = 0;
	if ( h > old )
		change = 1;
	else if ( h < old )
		change = 2;
	if ( !isdefined( source ) )
		source = "?";
	dev_log( "STREAK player=" + player GetEntityNumber() + " source=" + source + " best=" + best + " streak=" + s + " heat=" + old + "->" + h + " mult=" + heat_mult( player ) );
	// the STATE is live at once (the next roll reads it); what the player sees and hears of a change waits fb_secs
	// together, so the HUD's pulse and the sound land on the same beat
	if ( change != 0 )
		player thread streak_feedback( old, h, fb_secs );
	else
		player push_heat( 0 );
}

// PUBLIC: the streak ends with no pull (going down). Silent when there was no streak.
function streak_end( player, why )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return;
	had = ( isdefined( player.tod_luck_streak ) && player.tod_luck_streak > 0 );
	old = heat( player );
	player.tod_luck_streak = 0;
	player.tod_luck_heat = 0;
	if ( !had )
		return;
	dev_log( "STREAK player=" + player GetEntityNumber() + " source=" + why + " streak=0 heat=" + old + "->0" );
	if ( old > 0 )
		player thread streak_feedback( old, 0, 0 );
	else
		player push_heat( 0 );
}

// self = player. The HUD's copy (tod_upgrade.lua -> CoD.TodHeat, the luck plate's embers, the card panel and the
// spin screen): tod_luck_heat( heat, streak, change ), change 1 = it just rose, 2 = it just cooled, 0 = a refresh.
// A LuiNotifyEvent is a moment, not a state, so heat_resend_watch repeats it while hot.
function push_heat( change )
{
	if ( !isdefined( change ) )
		change = 0;
	s = 0;
	if ( isdefined( self.tod_luck_streak ) )
		s = self.tod_luck_streak;
	self LuiNotifyEvent( &"tod_luck_heat", 3, heat( self ), s, change );
}

// self = player. A change, seen and heard together: the HUD's copy (the chips pulse on a rise), an ignition rising
// to WARM / HEATING UP, a roar at ON FIRE (and the lobby hears who - the Legendary alert's free lane), a hiss when
// it ends. It pushes the CURRENT heat, so a later change that landed during the wait is never shown stale.
function streak_feedback( old, h, secs )
{
	self endon( "disconnect" );
	level endon( "end_game" );
	if ( isdefined( secs ) && secs > 0 )
		wait secs;
	change = 0;
	if ( h > old )
		change = 1;
	else if ( h < old )
		change = 2;
	self push_heat( change );
	if ( h > old )
	{
		if ( h >= TOD_STREAK_HEAT_MAX )
			self PlayLocalSound( "tod_heat_fire" );
		else
			self PlayLocalSound( "tod_heat_up" );
		if ( h >= TOD_STREAK_HEAT_MAX && old < TOD_STREAK_HEAT_MAX )
		{
			// the teammates (never the player himself): THE TOAST, kind 3, in our typeface (RT 2026-10-05; it was a
			// stock-font IPrintLnBold)
			self tod_upgrade_ui::team_toast( 3, 0, "tod_pull_alert" );
		}
	}
	else if ( h < old )
		self PlayLocalSound( "tod_heat_out" );
}

// self = player. While hot, the HUD hears the heat every TOD_STREAK_RESEND_SECS (a respawn or a menu rebuilds the
// HUD empty; a cold HUD needs nothing, cold is its default).
function heat_resend_watch()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	for ( ;; )
	{
		wait TOD_STREAK_RESEND_SECS;
		if ( heat( self ) > 0 )
			self push_heat( 0 );
	}
}

// The normalized zombie-kill award (last hit takes all).
function on_zombie_kill( attacker, b_headshot )
{
	amt = level.tod_luck_per_kill;
	if ( !isdefined( amt ) )
		amt = 1.0;
	if ( IS_TRUE( b_headshot ) )
		amt = amt * TOD_LUCK_HEADSHOT_MULT;
	add( attacker, amt );
}

// Boss LAST HIT takes the full luck award (user 2026-08-20). kind = the elite's
// tod_boss_kind ("mangler" | "doppelghast" | "dealer"), from each one's death watch.
function boss_kill( killer, kind )
{
	if ( isdefined( killer ) && IS_TRUE( killer.tod_is_partner ) )
		killer = killer.tod_partner_owner;
	if ( !isdefined( killer ) || !isplayer( killer ) )
		return;
	// v18.96 — ELITE KILL CONFIRM: red marker + ding for the killer, elites only
	// (user: "Zombies would get annoying"). This is the one call every elite
	// death already funnels through with its killer, so it hangs here.
	tod_killconfirm::elite_kill( killer, kind );
	add( killer, TOD_LUCK_ELITE );   // one rate for every elite (quiet: no spam)
}

// Door purchase (called from _tod_doors on a successful buy).
function door_buy( player )
{
	add( player, TOD_LUCK_DOOR );
	// (door text removed 2026-08-20 — user: no floaty text)
}

// ---------------------------------------------------------------------------
// Internals
// ---------------------------------------------------------------------------

function bar_of( player )
{
	if ( !isdefined( player.tod_luck_bar ) )
		player.tod_luck_bar = 0;
	return player.tod_luck_bar;
}

function set_bar( player, v )
{
	// v14.9: the TRUE clamp is the overcharge ceiling; TOD_LUCK_MAX is only
	// the top of the VISIBLE bar now (HUD, pips). The 100..150 band is the
	// secret — nothing on screen or in the ear distinguishes 100 from 149.
	if ( v > TOD_LUCK_OVERMAX )
		v = TOD_LUCK_OVERMAX;
	if ( v < 0 )
		v = 0;
	// SEGMENT PIP. Read the old value BEFORE the write, and fire only on an
	// UPWARD segment crossing. Two things this deliberately does not do:
	// it never pips on the post-event reset to 0 (that is a downward crossing
	// of every segment at once), and it never pips on a partial gain inside a
	// segment — the ear only hears the bar when it actually gains a notch.
	old = bar_of( player );
	player.tod_luck_bar = v;
	seg_old = int( old * TOD_LUCK_SEGS / TOD_LUCK_MAX );
	seg_new = int( v * TOD_LUCK_SEGS / TOD_LUCK_MAX );
	// Clamp BOTH to the HUD's segment count so the secret band is silent: the
	// 10th pip still fires once on crossing 100, and 110/120/130/140/150 fire
	// nothing (both sides read as "segment 10").
	if ( seg_old > TOD_LUCK_SEGS )
		seg_old = TOD_LUCK_SEGS;
	if ( seg_new > TOD_LUCK_SEGS )
		seg_new = TOD_LUCK_SEGS;
	if ( seg_new > seg_old )
		player thread segment_pip( seg_new );
	// OVERCHARGE edge: only set_bar can ever RAISE the bar (the direct writers
	// in _tod_upgrades only ever zero it), so the upward crossing
	// into 150 is fully owned here. The driver polls its own exit condition,
	// so the downward edge needs no code at all.
	player thread refresh_hud();
}

// self = player. One rung of the ladder. Threaded with a short delay so that on
// a headshot kill — which pays 1.5x and is the most likely thing to light a
// segment — the ding reads first and the pip answers it.
function segment_pip( seg )
{
	self endon( "disconnect" );
	level endon( "end_game" );
	if ( seg < 1 )
		seg = 1;
	if ( seg > TOD_LUCK_SEGS )
		seg = TOD_LUCK_SEGS;
	wait TOD_LUCK_PIP_DELAY;
	alias = "tod_luck_pip";
	if ( seg < 10 )
		alias = alias + "0";
	alias = alias + seg;
	self PlayLocalSound( alias );
}

// self = the dying zombie (zm_spawner death event contract); attacker = killer.
// Bosses never reach this (they are not zombie-archetype) — their luck pays
// from _tod_bosses' death paths.
function on_zombie_death( attacker )
{
	if ( !isdefined( attacker ) || !isplayer( attacker ) )
		return;
	// self.damagelocation is THE engine-set field (stock _zm_spawner reads it
	// everywhere; "damageloc" does not exist — verify pass 2026-08-20).
	// neck counts deliberately (stock is_headshot is head/helmet only).
	b_head = ( isdefined( self.damagelocation ) &&
	           ( self.damagelocation == "head" || self.damagelocation == "helmet" || self.damagelocation == "neck" ) );
	// HEADSHOT-KILL DING, shooter only (map 1's _acc_damage.gsc:1358 pattern —
	// PlayLocalSound is per-client, so full volume with no world falloff, and a
	// teammate's headshots never ring in your ears).
	//
	// KILL, not hit — the same call map 1 makes, and for the same reason: a ding
	// on every headshot HIT machine-guns against round-30 health pools.
	// on_zombie_death IS the death event, so it fires once per kill and needs no
	// bullet gate to stop AoE chains re-triggering it.
	//
	// Gated on b_head EXACTLY as the luck award is, deliberately: the ding then
	// means "that paid the 1.5x headshot bonus" and can never disagree with the
	// bar it is about to move.
	if ( b_head )
		tod_killconfirm::ding( attacker );   // v18.96: the ONE owner of the ding (once per frame — an elite headshot kill is both events)
	on_zombie_kill( attacker, b_head );
}

// ---------------------------------------------------------------------------
// Per-player watchers: HUD + revives + downs
// ---------------------------------------------------------------------------

function on_player_spawned()   // self = player (callback::on_spawned)
{
	self endon( "disconnect" );

	if ( !IS_TRUE( self.tod_luck_watchers_on ) )
	{
		self.tod_luck_watchers_on = true;
		self thread ensure_hud();
		self thread revive_watcher();
		self thread down_watcher();
		self thread heat_resend_watch();   // THE HOT STREAK's HUD copy (docs/201)
	}
	self thread refresh_hud();
	self push_heat( 0 );   // a fresh life's HUD learns the streak at once (cold is its default)
}

// Reviver credit: the stock revive notifies "player_revived" ON the revived
// player with the reviver as the arg (map 1's savior hook rides the same).
function revive_watcher()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	for ( ;; )
	{
		self waittill( "player_revived", reviver );
		if ( isdefined( reviver ) && isplayer( reviver ) && reviver != self )
		{
			add( reviver, TOD_LUCK_REVIVE );
			// (on-screen text removed 2026-08-20 — user: no floaty text)
		}
	}
}

// Down penalty + HUD SYNC: edge-detect the laststand transition, and
// self-heal the HUD against ANY direct bar writer (the upgrade event zeroes
// player.tod_luck_bar directly — the no-cycle direction; this poll catches
// it within 0.5s — verify pass 2026-08-20).
function down_watcher()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	was_down = false;
	shown = -1;
	paused_prev = false;   // dev log only: was a world pause (a card deal) up at the last poll
	for ( ;; )
	{
		wait 0.5;
		now = ( self laststand::player_is_in_laststand() );
		downed_now = false;
		if ( now && !was_down )
		{
			downed_now = true;
			drain( self, TOD_LUCK_DOWN );
			streak_end( self, "down" );   // THE HOT STREAK (docs/201): going down ends it
			// (on-screen text removed 2026-08-20 — user: no floaty text)
			// RAMPAGE (v14.36): the down also halves EVERY player's bar. Fired
			// AFTER the personal 25 so the downed player pays both, and placed
			// inside the same edge test so it can never double-fire on one down.
			// Threaded off, not called inline: party_down_drain touches every
			// player and each set_bar spawns a refresh_hud thread, and this poll
			// loop must not be the thing that stalls behind them.
			if ( TOD_LUCK_RAMPAGE_PARTY_DRAIN && IS_TRUE( level.tod_rampage_on ) )   // v16.59: switch OFF — see the define
				thread party_down_drain();
		}
		was_down = now;

		v = int( bar_of( self ) );
		paused_now = IS_TRUE( level.tod_upgrade_pause );
		if ( v != shown )
		{
			// THE SPEND RECORD: a card deal and the altar zero the bar by direct write
			// (_tod_upgrades), the Black Market through spend(). All three land here as
			// a drop to 0; a drop on the down edge is the down, not a spend.
			if ( v == 0 && shown > 0 && !downed_now )
			{
				r = level.round_number;
				if ( !isdefined( r ) )
					r = 0;
				dev_log( "SPENT player=" + self GetEntityNumber() + " bar=" + shown + " round=" + r + " deal=" + ( paused_now || paused_prev ) );
			}
			shown = v;
			self thread refresh_hud();
		}
		paused_prev = paused_now;
	}
}

// Dev-only console record (the map's PrintLn pattern: the string is built outside the
// developer block, the call stays inside it). Diagnostics never touch the bar.
function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_LUCK] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// ---------------------------------------------------------------------------
// The bar (all-LUI): push bar/10 into the todUpgLuck clientfield; the Lua
// (tod_upgrade.lua) swaps in the baked i_tod_luck_NN image for that level —
// gold-at-hot (8..9) and the MAX state are baked into the art.
// ---------------------------------------------------------------------------

function ensure_hud()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	self thread refresh_hud();
}

function refresh_hud()   // self = player
{
	self tod_upgrade_ui::set_luck_pct( bar_of( self ) );
}
