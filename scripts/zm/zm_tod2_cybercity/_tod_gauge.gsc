// =============================================================================
// _tod_gauge.gsc — the TOWER GAUGE feed (the HUD floor indicator).
//
// Publishes TWO events to each player's HUD, both int-only and both
// change-gated:
//   tod_floor (2 args)  the cell THEY are on, and the cell the lowest live
//                       boss is on (0 = none)
//   tod_down  (2 args)  a BITMASK of the cells that have a DOWNED TEAMMATE on
//                       them, split into a low and a high half (0,0 = nobody)
// The Lua (tod_upgrade.lua) draws the gauge from those — dark backing, one lit
// cell stamped per climbed floor, a red pip beside the boss's cell, and any
// number of cells swapped to the red DOWN tile.
//
// WHY LuiNotifyEvent AND NOT A CLIENTFIELD: the clientuimodel budget is at
// its PROVEN 61-bit ceiling (18 fields, APPEND ONLY — see _tod_upgrade_ui).
// A floor + boss-floor pair would cost ~10 more bits, and the down mask 25
// more on top. The int-only LuiNotifyEvent lane costs ZERO clientuimodel bits,
// which is exactly why the boss banner and the owned-upgrades sync already
// ride it.
//
// WHY THE DOWN MASK IS SPLIT ACROSS TWO ARGS AND SENT ON ITS OWN EVENT, and
// not appended as a third arg to tod_floor (v14.50 — both halves of this are
// a deliberate refusal to be the first caller of something unproven):
//   (a) 25 cells is 25 BITS, up to 33,554,431 as one number, and this lane's
//       values land in the LUI model system, which the client Lua reads back
//       through tonumber()/math.floor — i.e. as a Lua number, with no promise
//       anywhere that the value survived as an exact 32-bit int. A float32
//       carries integers exactly only to 16,777,216: above that the spacing is
//       2, so "cell 25 AND cell 1 are down" (16,777,217) would quietly lose
//       cell 1. Nothing in this tree or in stock pushes a value that big
//       through here, so it is unproven, and the failure mode is a marker that
//       silently does not draw — the exact bug this feature exists to fix.
//       Split 13 + 12, every value is <= 8191 and the question never arises.
//   (b) ARITY. This tree's proven shapes are 2 and 3 args; stock MP ships 4, 5
//       and 7 (_hud_message.gsc:325/443), so a 4-arg call is very likely fine
//       — but "very likely fine" is how a silent no-fire gets shipped, and a
//       second 2-arg event costs one #precache and buys certainty. It also
//       decouples the feeds: a party climbing pushes floor events all match
//       without ever touching the down lane, and vice versa.
//
// TRAP (paid for twice on this map): the event string MUST be #precache'd or
// LuiNotifyEvent silently never fires.
//
// Floors: the tower is TOD_GAUGE_LAPS (50) laps of LAP_RISE 384 starting at
// z=0, roof at 19200. The BAR has only 25 cells, so floor_of() folds two
// floors into one cell (v8 — "you need to open double the doors to see
// progress on the tower bar"):
//   z < 0            -> 0  (base arena; gauge shows no lit cells)
//   0 <= z < 19200   -> cell 1..25   (real floor 1..50)
//   z >= 19200       -> 26 (roof — the crown lights)
// (This block said "25 laps ... roof at 9600" until 2026-08-30; it was never
// updated through the v8 doubling. The DEFINES are the source of truth.)
//
// IT ALSO OWNS THE FLOOR HIGH-WATER. Since v14.35 this module's poll records
// the highest REAL floor each player has stood on (real_floor_of /
// floor_reached), because the CLASS TIER promotion is gated on it: tier 2
// needs floor 10, tier 3 needs floor 30 (20 until 2026-09-02). That is a gameplay rule reading a
// HUD module's number, which is the right way round — the gate is written
// against the floor the player can literally see on their own gauge.
// =============================================================================

#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;
#using scripts\zm\zm_tod2_cybercity\_tod_classes;   // [tod v17.33] pap_tier — the HUD badge feed
#using scripts\zm\zm_tod2_cybercity\_tod_arena_data;   // GENERATED — in_arena(): the Battle Arena room is not a floor (2026-09-28)
#using scripts\zm\zm_tod2_cybercity\_tod_house_data;   // GENERATED - in_house / in_parlour: THE DEALER'S HOUSE is not a floor either (docs/207)

#insert scripts\shared\shared.gsh;

// v8 (user 2026-08-21): the tower DOUBLED to 50 floors but the gauge art still
// has 25 cells, so ONE CELL = TWO FLOORS — "you need to open double the doors
// to see progress on the tower bar". floor_of() reports the CELL, not the
// floor: cell = ceil(floor / 2).
#define TOD_GAUGE_LAP_RISE   384
#define TOD_GAUGE_LAPS       50    // real floors
#define TOD_GAUGE_CELLS      25    // cells on the bar art
#define TOD_GAUGE_ROOF_ID    26    // = CELLS + 1
#define TOD_GAUGE_TICK       0.35   // push cadence; only sends on CHANGE
// real_floor_of ONLY. A player standing on a landing has their feet AT the
// landing's z, and that z is the exact boundary between two floors — one
// ground-trace hair under it reads as the floor below, which would make
// "reached floor 10" flicker for someone standing on floor 10. 8 units is a
// little over half a stair riser: it cannot promote anyone who has not
// actually arrived, and it cannot demote anyone who has.
#define TOD_GAUGE_FLOOR_EPS  8
// The DOWN mask's split point: cells 1..13 ride the low arg (bits 0..12) and
// cells 14..25 the high one (bits 0..11), so neither number can exceed 8191.
// LOCKSTEP with GA_SPLIT in tod_upgrade.lua — the Lua reassembles by the same
// boundary, and there is no way for the two to disagree loudly.
#define TOD_GAUGE_MASK_SPLIT 13
// docs/160 — THE DESCENT. Tower of Doom II starts at the crown and goes DOWN,
// so the CLASS TIER gate's "have you climbed far enough" becomes "have you
// descended far enough": the same per-player alive-only poll keeps a LOW-
// water mark (tod_floor_low, only ever falls) beside the high-water, and
// tier_progress() — the one number _tod_upgrades' floor gate reads — is the
// FLOORS DESCENDED from the top (LAPS - low). The requirements do not move
// (10 floors for tier 2, 30 for tier 3 — TOD_TIER2/3_FLOOR); what the player
// is told is the FLOOR they will be on when they clear it, tier_floor_display
// (40 and 20). LOCKSTEP with DESCENT in gen_tower_map.js and TIER_DESCENT in
// tod_upgrade.lua. With 0 the climb's high-water gate is live again.
#define TOD_GAUGE_DESCENT    1

#precache( "eventstring", "tod_floor" );
// v14.50 — the downed-teammate cells. Its own event, deliberately (see the
// header). SAME PRECACHE TRAP as tod_floor: without this line LuiNotifyEvent
// silently never fires and the red cells simply never appear, with no error.
#precache( "eventstring", "tod_down" );
// [tod 2026-08-21] real MAX HP for the Aetherium HP text (the kit's health
// field is a 0..1 fraction and its Lua multiplied by a hardcoded 100, so
// the map's 150-HP players read "100 HP"). Same zero-bit int lane, sent
// only when a player's maxhealth changes (spawn, jugg, upgrades).
#precache( "eventstring", "tod_maxhp" );
// [tod v17.25] THE ROUND READOUT. The top-right "ROUND n" is ours now — the
// stock ZmRndContainer was deleted out of AetheriumRoundCounter.lua and the
// number is set in the map's own baked typeface (user 2026-09-04: "Lets remove
// stock and track ourselves"). One int, change-gated, and it rides here rather
// than in a module of its own because this loop is already the map's per-player
// HUD-push heartbeat and already owns the per-life re-arm contract.
//
// WHY NOT A CLIENTFIELD: the clientuimodel pool is at 60 of its PROVEN 61 bits
// (_tod_upgrade_ui.gsc) and a round number wants ten. This lane costs none.
// SAME PRECACHE TRAP as every event above: no line, no fire, no error.
#precache( "eventstring", "tod_round" );
// [tod v17.33] THE PACK-A-PUNCH TIER BADGE on the gun HUD — 0 unpacked, 1
// packed (2..3 were the Endless Spire's re-packs; the spire was removed
// 2026-09-29). Reports the tier of the weapon CURRENTLY
// IN HAND, so it changes on a weapon switch as well as on a purchase.
//
// WHY IT RIDES HERE and not a clientfield: the clientuimodel pool is at 60 of
// its PROVEN 61 bits (_tod_upgrade_ui.gsc's own count), and a 0..3 value wants
// two. The only dead field, todMagBonus, is one bit — so a clientfield would
// have to take bits out of a shipped feature to buy a badge. This lane costs
// none, and this loop is already the map's per-player HUD-push heartbeat with
// the per-life re-arm contract the badge needs.
//
// SAME PRECACHE TRAP as every event above: no line here, no fire, no error.
#precache( "eventstring", "tod_pap_tier" );

#namespace tod_gauge;

function init()
{
	level thread gauge_loop();
}

function gauge_loop()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );

	for ( ;; )
	{
		wait TOD_GAUGE_TICK;

		boss_f = boss_floor();

		foreach ( p in GetPlayers() )
		{
			if ( !isdefined( p ) || !isplayer( p ) )
				continue;

			// THE CLASS TIER FLOOR GATE's input (v14.35, user 2026-08-30: "you
			// must also reach floor 10 to get 2nd tier class upgrade and floor
			// 20 for 3rd"; T3 moved to floor 30 on 2026-09-02). A per-player HIGH-WATER of the REAL floor, read by
			// _tod_upgrades::tier_floor_ok. Tracked HERE because this is the
			// map's only per-player altitude poll — and ABOVE the change-only
			// `continue` further down, which is about the HUD send and must
			// never decide whether progress was recorded.
			//
			// ALIVE + PLAYING ONLY. A dead player spectates a teammate and
			// their .origin rides that camera, so sampling a spectator would
			// hand a body sitting in the base arena the climber's floor —
			// exactly the free ride the gate exists to close. LAST STAND still
			// samples (sessionstate stays "playing" and isalive is TRUE there —
			// map 1's down-path lesson), which is correct: a downed player
			// really is standing on that floor.
			//
			// NOT IN THE BATTLE ARENA (2026-09-28): the arena room stands at
			// z 0, which real_floor_of reads as floor 1, so one trip from the
			// floor-40 chamber stamped a low-water of 1 = 49 floors descended
			// and cleared BOTH tier gates (floors 40 and 20) at once.
			if ( IsAlive( p ) && ( !isdefined( p.sessionstate ) || p.sessionstate == "playing" ) && !tod_arena_data::in_arena( p.origin ) && !tod_house_data::in_house( p.origin ) && !tod_house_data::in_parlour( p.origin ) )
			{
				rf = real_floor_of( p.origin[ 2 ] );
				if ( !isdefined( p.tod_floor_best ) || rf > p.tod_floor_best )
					p.tod_floor_best = rf;
				// docs/160: the LOW-water, for the descent's tier gate. Same
				// sample, same alive-only rule, opposite direction. Never
				// stamped below the plaza (0): the Undercity is below the
				// tower, not a floor of it, and 0 already clears every gate.
				if ( !isdefined( p.tod_floor_low ) || rf < p.tod_floor_low )
					p.tod_floor_low = rf;
			}

			// MAX HP feed (change-only; a fresh HUD reads the default until the
			// first push, which lands on this tick's change from undefined)
			if ( isdefined( p.maxhealth ) && p.maxhealth > 0 )
			{
				mh = int( p.maxhealth );
				if ( !isdefined( p.tod_gauge_mh ) || p.tod_gauge_mh != mh )
				{
					p.tod_gauge_mh = mh;
					p LuiNotifyEvent( &"tod_maxhp", 1, mh );
				}
			}

			// THE ROUND READOUT (v17.25). level.round_number is the number the
			// SERVER acts on — the boss cadence, the spawn budget and the
			// zombie-speed ramp all read it — so the HUD shows that and not a
			// stock counter reached through three replaced round functions.
			// Change-gated like every other lane here; re-armed per life by
			// _tod_upgrade_ui::player_lui_life clearing tod_round_shown,
			// because the kit HUD is rebuilt by the engine on every spawn and a
			// change-only feed says nothing to a fresh menu.
			if ( isdefined( level.round_number ) && level.round_number >= 1 )
			{
				rn = int( level.round_number );
				if ( !isdefined( p.tod_round_shown ) || p.tod_round_shown != rn )
				{
					p.tod_round_shown = rn;
					p LuiNotifyEvent( &"tod_round", 1, rn );
				}
			}

			// THE PACK-A-PUNCH TIER BADGE (v17.33). Change-gated like every
			// lane here, and re-armed per life by _tod_upgrade_ui's
			// player_lui_life clearing tod_pap_tier_shown.
			//
			// READS THE WEAPON IN HAND, not a stored per-player number: the
			// tier is per-GUN (a packed gun can sit beside an unpacked one), so
			// the badge has to follow the switch.
			// That makes this the one lane here whose value can change without
			// any game state changing at all, which is exactly why it is polled
			// on the heartbeat rather than pushed from the purchase site.
			pt = 0;
			if ( IsAlive( p ) )
			{
				cw = p GetCurrentWeapon();
				if ( isdefined( cw ) && cw != level.weaponNone )
					pt = tod_classes::pap_tier( p, cw );
			}
			if ( !isdefined( p.tod_pap_tier_shown ) || p.tod_pap_tier_shown != pt )
			{
				p.tod_pap_tier_shown = pt;
				p LuiNotifyEvent( &"tod_pap_tier", 2, pt, 0 );
			}

			// (THE FINALE's song clock that took this bar over during extraction -
			// finale_cell - retired whole with the Map One ending, 2026-10-05.)
			f = floor_of( p.origin[ 2 ] );
			dm = down_mask_for( p );

			// THE DOWN LANE, change-gated on its own and sent ABOVE the floor
			// lane's `continue` — a teammate going down, crawling to another
			// cell, or being revived must push whether or not this player's own
			// floor moved, and standing still is the normal case for the person
			// who most needs to see it.
			if ( !isdefined( p.tod_gauge_dlo ) || p.tod_gauge_dlo != dm[ 0 ]
			  || !isdefined( p.tod_gauge_dhi ) || p.tod_gauge_dhi != dm[ 1 ] )
			{
				p.tod_gauge_dlo = dm[ 0 ];
				p.tod_gauge_dhi = dm[ 1 ];
				p LuiNotifyEvent( &"tod_down", 2, dm[ 0 ], dm[ 1 ] );
			}

			// Send only on change — this loop runs forever, and a per-tick
			// event for every player would be pure config-string churn.
			if ( isdefined( p.tod_gauge_f ) && p.tod_gauge_f == f
			  && isdefined( p.tod_gauge_bf ) && p.tod_gauge_bf == boss_f )
				continue;

			p.tod_gauge_f = f;
			p.tod_gauge_bf = boss_f;
			p LuiNotifyEvent( &"tod_floor", 2, f, boss_f );
		}
	}
}

// -> the CELL index on the bar (1..CELLS), 0 = base arena, CELLS + 1 = the
// roof. The tower stacks LAP_RISE floors from z = 0.
function floor_of( z )
{
	laps = TOD_GAUGE_LAPS;
	cells = TOD_GAUGE_CELLS;
	if ( z >= laps * TOD_GAUGE_LAP_RISE )
		return cells + 1;
	if ( z < 0 )
		return 0;
	f = 1 + int( z / TOD_GAUGE_LAP_RISE );      // real floor 1..laps
	if ( f > laps )
		f = laps;
	if ( f < 1 )
		f = 1;
	c = int( ( f + 1 ) / 2 );                   // 2 floors per cell (ceil)
	if ( c > cells )
		c = cells;
	if ( c < 1 )
		c = 1;
	return c;
}

// ---------------------------------------------------------------------------
// THE DOWNED-TEAMMATE CELLS (v14.50, user 2026-08-31: "players dont know where
// their tm8s are when they go down ... makes a section light red if a player is
// down at that location").
//
// A BITMASK, NOT A CELL NUMBER, and that is the whole design decision (user,
// same day: "there is always a possibility that multiple players are down at
// different areas so we need to be prepared to have multiple squares red ...
// I dont want the system to break cause it doesnt expect 2,3 players down at
// once"). Bit (cell-1) is set for every cell holding at least one downed
// teammate, so the Lua walks 25 bits and never needs to know how many people
// are down — one, two or three reds cost the same code path, and there is no
// "the" down cell anywhere in this feature to be wrong about.
//
// `|` AND NEVER `+`. Two players down on the SAME cell is the case a sum gets
// wrong (bit 4 + bit 4 = bit 5 — a red cell one floor above where anybody
// actually is). OR is idempotent, so the same cell set twice is the same mask,
// which makes the collision case correct by construction rather than by a
// guard somebody has to remember.
//
// PER VIEWER, EXCLUDING THEIR OWN BODY: a downed player knows where they are,
// so red on this gauge means exactly one thing — "a teammate is there and
// needs you". Solo therefore never sees a red cell at all, which is right.
//
// -> a TWO-ELEMENT array of 13-bit chunks: [k] holds cells 13k+1 .. 13k+13.
// The split is a transport concern, not a design one (see the header): it
// keeps every number under 8191 so no float rounding can eat a bit. [0],[1]
// ride tod_down. Callers hand them straight to the event and never interpret
// them. LOCKSTEP with GA_SPLIT in the Lua, which unpacks by the same
// chunk/bit arithmetic.
// ---------------------------------------------------------------------------
function down_mask_for( viewer )
{
	m = [];
	m[ 0 ] = 0;
	m[ 1 ] = 0;

	foreach ( q in GetPlayers() )
	{
		if ( !isdefined( q ) || !isplayer( q ) || q == viewer )
			continue;

		// LAST STAND ONLY, and IsAlive is what separates it from a corpse:
		// isalive stays TRUE through last stand (map 1's down-path lesson) and
		// goes FALSE once the player has bled out. That is exactly the line
		// this marker wants — a bled-out player cannot be revived, so sending
		// the party 30 floors to their body would be a lie. And
		// player_is_in_laststand() reads the revive trigger's existence, so it
		// clears itself the frame a revive completes; nothing here has to
		// watch for the revive.
		if ( !IsAlive( q ) || !( q laststand::player_is_in_laststand() ) )
			continue;

		c = down_cell_of( q.origin[ 2 ] );
		chunk = int( ( c - 1 ) / TOD_GAUGE_MASK_SPLIT );
		bit = ( c - 1 ) - ( chunk * TOD_GAUGE_MASK_SPLIT );
		m[ chunk ] = m[ chunk ] | ( 1 << bit );
	}
	return m;
}

// -> a cell the gauge can actually DRAW (1..CELLS) for any world z.
//
// The same clamp the boss pip already pays for, for the same reason, and the
// direct answer to the user's "or at least pick the closest section ... catch
// the edge cases where they may be in between section or something": every z
// between the base deck and the roof already lands in a cell by construction
// (floor_of has no gaps), so the only real edge cases are the two ENDS. A down
// in the base arena reads z < 0 -> 0, and a down on the roof, the causeway or
// the crown reads ROOF_ID 26; neither is a drawable cell, and a mask bit for
// either would render nowhere at all — "nobody is down" at the exact moment
// somebody is. Pinning them to the bottom and top cells puts the mark on the
// nearest section to where that player physically is.
function down_cell_of( z )
{
	c = floor_of( z );
	cells = TOD_GAUGE_CELLS;
	if ( c < 1 )
		c = 1;
	if ( c > cells )
		c = cells;
	return c;
}

// -> the REAL floor (1..LAPS), 0 = below the base arena deck.
//
// floor_of()'s ungrouped sibling, and deliberately NOT built on top of it: the
// gauge folds two floors into one art cell and pins everything at or above the
// roof to ROOF_ID, both of which are answers about the BAR, not about the
// tower. This one is the answer about the tower, so a gate can be written
// against the floor numbers the player actually reads on their HUD
// ("floor 10", not "cell 5"). It clamps at LAPS, so the crown and the causeway
// report the top floor rather than running off the end — both are above every
// gate by construction.
function real_floor_of( z )
{
	if ( z < 0 )
		return 0;
	f = 1 + int( ( z + TOD_GAUGE_FLOOR_EPS ) / TOD_GAUGE_LAP_RISE );
	if ( f > TOD_GAUGE_LAPS )
		f = TOD_GAUGE_LAPS;
	return f;
}

// PUBLIC — the highest REAL floor this player has stood on this match.
// 0 until the first poll. It only ever RISES, so a player who climbs to a
// breather and then rides a teleporter back to the base keeps what they
// earned; the gate asks "have you been there", not "are you there now".
// Lives on the player entity, which survives death and respawn the same way
// tod_tier and tod_levels do.
function floor_reached( player )
{
	if ( !isdefined( player ) || !isdefined( player.tod_floor_best ) )
		return 0;
	return player.tod_floor_best;
}

// PUBLIC — stamp the high-water at the top of the tower.
//
// For paths that put a player above every gate by construction and must not
// wait on the 0.35s poll to notice: the dev max-out
// (_tod_upgrades::dev_grant_maxed) runs its tier_up ladder right after this,
// and a grant is not a thing that may fail on a sampling race.
function mark_top_reached( player )
{
	if ( !isdefined( player ) )
		return;
	player.tod_floor_best = TOD_GAUGE_LAPS;
	player.tod_floor_low = 0;   // docs/160: "above every gate" is "below every gate" on the descent
}

// PUBLIC (docs/160) — the FLOORS DESCENDED from the top this player has
// earned this match: LAPS minus the lowest real floor they have stood on. 0
// until the first poll and 0 at the crown itself (real_floor_of clamps the
// crown, the causeway and the terrace to LAPS). Only ever rises, like the
// high-water: a player who rides a teleporter back UP keeps it.
function floors_down( player )
{
	if ( !isdefined( player ) || !isdefined( player.tod_floor_low ) )
		return 0;
	d = TOD_GAUGE_LAPS - player.tod_floor_low;
	if ( d < 0 )
		d = 0;
	return d;
}

// PUBLIC — THE ONE NUMBER the CLASS TIER floor gate reads
// (_tod_upgrades::tier_floor_ok and its toasts): floors climbed on the
// climb layout, floors descended on the descent (TOD_GAUGE_DESCENT).
function tier_progress( player )
{
	if ( TOD_GAUGE_DESCENT )
		return floors_down( player );
	return floor_reached( player );
}

// PUBLIC — the FLOOR NUMBER a player is told for a requirement of `need`
// floors of progress: the floor itself on the climb, LAPS - need on the
// descent ("tier 2 unlocks at floor 40"). What the badge, the toasts and the
// pause row print; the requirement itself never moves.
function tier_floor_display( need )
{
	if ( TOD_GAUGE_DESCENT )
		return TOD_GAUGE_LAPS - need;
	return need;
}

// The LOWEST live boss (they spawn at the base and climb, so the lowest one is
// the one still coming for you). 0 = no boss alive.
//
// There is no level-side boss array — _tod_bosses marks the entities
// themselves with `.is_boss` (Panzer :599, Rogue Protector :956) and the
// module's own sweeps identify them the same way (:457, :1021). Match that.
function boss_floor()
{
	team = ( isdefined( level.zombie_team ) ? level.zombie_team : "axis" );
	ai = GetAITeamArray( team );

	best = 0;
	cells = TOD_GAUGE_CELLS;
	foreach ( b in ai )
	{
		if ( !isdefined( b ) || !IsAlive( b ) )
			continue;
		if ( !IS_TRUE( b.is_boss ) && !IS_TRUE( b.acc_is_boss ) && !IS_TRUE( b.acc_is_mini_boss ) )
			continue;
		f = floor_of( b.origin[ 2 ] );
		// CLAMP BOTH ENDS (audit 2026-08-25). floor_of() returns 26 (ROOF_ID) for
		// anything at or above the roof, and the Lua only draws the pip for
		// 1..CELLS(25) — so a Panzer on the rooftop arena made the pip VANISH,
		// reading as "no boss" at the exact moment there certainly is one.
		// Pinning it to the top cell puts it where the crown is, which is true.
		if ( f <= 0 )
			f = 1;
		if ( f > cells )
			f = cells;
		if ( best == 0 || f < best )
			best = f;
	}
	return best;
}
