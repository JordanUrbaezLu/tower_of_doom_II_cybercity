// =============================================================================
// _tod_ammo_crate.gsc — a buyable AMMO CRATE on every breather balcony, plus
// one in the CROWN HALL (v12)
// (user 2026-08-24: "adding an ammo box at every breather area? Will cost 5k
// for ammo. We have these ammo crates from the other map we can just reuse";
// user 2026-08-26: "we need an ammo crate in that room").
//
// WHY IT BELONGS HERE: the breathers are the map's only rest stops, and this
// map has NO mystery box and NO wallbuys — every round of ammo comes from the
// class gun's reserve, SCAVENGER, BULLET FEED or a Max Ammo drop. Past ~round
// 25 the reserve curve goes negative and there is nothing to spend points on
// mid-climb. A flat 5k refill at the four rest stops is the sink.
//
// PORTED from map 1's _acc_ammo_crate.gsc. v13.23 (user 2026-08-29): pricing
// is BY PAP STATE again — 2500 for a base gun, 5000 for a PaP'd one (map 1's
// own scheme, minus the wonder tier), applying to EVERY crate. The original
// tower spec was a flat 5000; that lasted 2026-08-24 -> 08-29. Same asset,
// same script-spawn recipe. A SIXTH crate sits at the BASE (core WEST face
// since v14.2 — the v13.23 east-face spot sat under lap 1's east flight and
// its script-clip carves severed the stair navmesh; see the long note in
// spawn_all). Since v14.3 ALL SIX static crates share one contract: origin
// from generated data, collision a generator-cut clip brush in the .map.
// v17.38 (user 2026-09-04: "master ammo crates so we dont ever have to touch
// them again"): EVERY crate in the map is on that contract now. There are no
// script clips left anywhere (crate_clips() is gone), the facing is one convention
// (gen_tower_map.js CRATE_YAW_*: front = yaw + 90), the occupancy box is
// rotated to each crate's real yaw by crateBox(), and the trigger recipe
// below reads its two numbers out of GENERATED _tod_breather_data.gsc.
//
// ASSET: the [West] Ammo Crates pack (Westchief596; ZeRoY's S4 ammo-crate model
// + textures). The GDT lives INSTALL-SIDE at
// <modtools>\source_data\acc_west_ammo_crate.gdt and is SHARED WITH MAP 1 —
// referenced only, never edited (the shared-GDT rule: editing it would retune
// map 1). Our side is one `xmodel,west_ammo_crate_model` zone line.
//
// SCALE 2.5x, inherited from map 1's live tuning (user there 2026-07-12: "these
// tiny boxes you have to look down to even see"). The raw model is ~29x33x25
// units — knee-high — so at 2.5x it reads as a real crate at ~72x83x63.
//
// COLLISION LIVES IN THE .map, NOT HERE (v10.25, user 2026-08-24: "Also the
// ammo crates dont have clips"). v10.22 spawned this model NOT SOLID on
// purpose and that call is now reversed — you could walk through the crates.
//
// It could not be fixed on this side. The xmodel has NO collision data at all
// (acc_west_ammo_crate.gdt: CollisionMap "" and BulletCollisionFile ""), so
// Solid() on the script_model has nothing to switch on; and a script-spawned
// clip entity would need DisconnectPaths and would still be invisible geometry
// standing on a walkable balcony, which is precisely what
// lint_tod_geometry CHECK 1 exists to catch.
//
// So tools/gen_tower_map.js emits a clip brush tucked inside the crate mesh
// (search "ammo crate body"). v13 closed the old drift trap: the breather
// crate origin now lives ONCE, in the generator's BR_FURN table, which cuts
// that clip AND emits _tod_breather_data.gsc::crate_org() — this file reads
// the same value the brush was cut from, so clip and model cannot separate.
//
// STILL NOT GSC-ONLY: moving the crate means editing BR_FURN in the
// generator, and that is a regen + full build + LED bake.
// =============================================================================

#using scripts\shared\flag_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;

#using scripts\zm\_zm_score;      // can_player_purchase / minus_to_player_score
#using scripts\zm\_zm_utility;    // is_player_valid
#using scripts\zm\_zm_weapons;    // is_weapon_upgraded (v13.23 two-tier pricing)

#using scripts\zm\zm_tod2_cybercity\_tod_breather_data;   // crate_org/yaw + breather_zs (GENERATED, v13)
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;   // crown_crate_org/yaw (GENERATED)

#insert scripts\shared\shared.gsh;

// The crate model. Precache AFTER every #using/#insert — the "No generated
// data" compile trap (CLAUDE.md GSC dialect).
#precache( "model", "tod_ammo_chest" );   // docs/208: Nikolai's AMMO BOX V6 (map 1's v19.69b), built at game size

#define TOD_CRATE_COST_BASE 2500  // non-PaP'd weapon (user 2026-08-29: "2500 for non pap")
#define TOD_CRATE_COST_PAP  5000  // PaP'd weapon (was the flat price for everything, 2026-08-24 -> 08-29)
// (TOD_CRATE_SCALE 2.5 retired, docs/208: the V6 ships at its game size - no SetScale)
// THE TRIGGER (v17.38, user: "check the trigger on all ammo crates. Some of them
// are off and you cant get ammo unless at a certain angle"). Radius and
// front-offset come from GENERATED _tod_breather_data.gsc (crate_trig_r /
// crate_trig_out) — the same numbers the generator asserts against every other
// vendor trigger. WHY THE OFFSET: the trigger used to sit ON the model origin
// with radius 72, and the crate's own collision holds a player's origin
// >= 38 + ~16 (capsule) = 54u from that origin — an 18u usable band, only on
// the face's centre line. Off-axis by a step, or standing naturally, and there
// was no prompt. The trigger now sits crate_trig_out() (56) IN FRONT of the
// origin, the stations' and PaP machines' own grammar, so the band runs from
// the face to ~128u out and ±72 across it. Height and lift unchanged: the
// cylinder tests the player's bounding box (memory trigger-origin-under-decal)
// and +40 keeps the origin above every 1u floor decal in the map.
#define TOD_CRATE_TRIG_H    80
#define TOD_CRATE_TRIG_LIFT 40

#namespace tod_ammo_crate;

// PLACEMENT — one per breather lounge, EAST wall, facing west into the room
// (unchanged by v13: the crate was fine where it was — it was the PaP that
// crowded it, and the PaP moved to the W wall). The origin comes from
// GENERATED _tod_breather_data.gsc, cut from the generator's BR_FURN table,
// which also cuts the collision clip and asserts this trigger clears every
// other lounge trigger by both radii + 64. CRATE FACING (v17.37): front =
// yaw + 90 — 90 faces WEST (-x), 270 EAST, 0 NORTH, 180 SOUTH. The old note
// here ("0 = front toward -y, 90 = +x, 270 = -x") was the belief every tower
// crate was placed under, and it was backwards; gen_tower_map.js CRATE_YAW_*
// carries the record.

function init()
{
	level thread spawn_all();
}

function spawn_all()
{
	level endon( "end_game" );

	// Wait for the blackscreen like every other scripted fixture — the
	// balconies are .map geometry present from frame one, but spawning props
	// pre-blackscreen races the stock world init.
	level flag::wait_till( "initial_blackscreen_passed" );

	// THE BASE CRATE (v13.23, user 2026-08-29: "add an ammo crate at spawn").
	//
	// v14.3 — PERFECTED: origin/yaw now ride GENERATED _tod_breather_data.gsc
	// (base_crate_org/base_crate_yaw) and the collision is a generator-cut
	// "base ammo crate body" clip brush in the .map, exactly like the other
	// five crates — NO script clips, NO DisconnectPaths, nothing here the
	// geometry lint can't see. The generator (gen_tower_map.js BASE_CRATE)
	// also ASSERTS the box clear of the lap-1 E flight and the west walkway
	// >= 128u, so the v13.23 mistake is now mechanically impossible.
	//
	// THE HISTORY THAT FORCED THIS (keep it — it is the whole design): v13.23
	// hand-placed the crate at (320,0,0), "the emptiest documented base wall"
	// — empty because LAP 1'S EAST FLIGHT RUNS OVER IT (x[256,416]; the same
	// strip the teleport bay was moved out of in v10.25). Its three
	// script-clip DisconnectPaths carves severed the stair navmesh BOTH ways
	// (Workshop report Pinkbrotha4310 2026-08-30: zombies below wouldn't
	// climb, zombies above wouldn't come down). v14.2 moved it to the core
	// WEST face (-320,0,0), yaw 270, still with script clips; v14.3 moved the
	// truth into the generator. The west face is clear by construction: W
	// flights belong to EVEN laps, so the first stair over this strip is lap
	// 2's at z=384.
	place( tod_breather_data::base_crate_org(), tod_breather_data::base_crate_yaw() );

	// Lounge mid-slab heights — the same generated list every other piece of
	// breather furniture reads ((lap-1)*LAP_RISE + 192, laps 10/20/30/40).
	zs = tod_breather_data::breather_zs();

	for ( i = 0; i < zs.size; i++ )
		place( tod_breather_data::crate_org( zs[ i ] ), tod_breather_data::crate_yaw() );

	// THE CROWN HALL CRATE (v12, user 2026-08-26: "we need an ammo crate in
	// that room") — RETIRED in TOD II (docs/160, user 2026-09-23: "similar to
	// Moon, I do want to clean out the crown so there's no ammo crates or
	// anything. What I do want to add is a pack-a-punch"). The hall is the
	// SPAWN now and carries the Pack-a-Punch and nothing else; the generator
	// no longer cuts the crate's clip (CROWN_CLEAN). The anchor is still
	// emitted, so restoring the crate is this one line plus that flag.
	// place( tod_crown_data::crown_crate_org(), tod_crown_data::crown_crate_yaw() );
}

// =============================================================================
// ONE CRATE, ONE RECIPE (v14.58, user 2026-08-31: "All ammo crates should work
// the same"). The three functions below are the WHOLE definition of an ammo
// crate — model, trigger and hint — and place() is the one spawner. (The
// retired Endless Spire once hand-rolled its own COPY of the hint literal: two
// copies of a string that names two prices is exactly the drift trap this
// repo keeps paying for, and it spent TWO permanent triggerstring slots for
// one prompt.) One literal and one slot for every crate in the map.
// =============================================================================

// THE HINT. Read the triggerstring budget note before touching this: a DISTINCT
// string is a PERMANENT engine slot, cap 250 a match, never freed (CLAUDE.md
// "TRIGGERSTRING BUDGET"). This function existing is what keeps every crate on
// ONE slot — call it, never re-type the literal.
//
// COPY (user 2026-08-31: "We shoudl say Regulat $2500 and Pack a Punch $5000").
//
// GRAMMAR — PromptDefault.lua parses this into a structured card:
//     Hold [btn] <TITLE> - <detail 1> / <detail 2> [Cost: N]
// so this renders as the title "AMMO CRATE" over two detail lines,
// "Regular $2500" and "Pack a Punch $5000". Leading with the NOUN is required:
// the card drops "Hold [btn]" and draws its own key glyph, so a line that began
// with "for"/"to" would reach the screen as a dangling fragment.
//
// "PACK A PUNCH" IS ONLY SAFE HERE BECAUSE THE ROUTER CLAIMS THE NOUN FIRST.
// ZMCursorHintNew.lua's isPAPHint() sends anything containing both "pack" and
// "punch" to the Pack-a-Punch card; classifyHint() tests the TOD_NOUNS list
// (which holds "ammo crate") BEFORE it, so this line lands on the default card.
// If you rename this prompt, rename it in TOD_NOUNS in the same commit.
//
// NO "[Cost: N]" BRACKET, deliberately: there are two prices and the card has
// one price row. The card reads the "$" and still says "To Buy" in its footer.
//
// THIS STRING MUST STAY CONSTANT. Every crate's spawn_trigger — and therefore
// SetHintString — hands over these same characters, which is why every crate
// shares ONE slot. Interpolate any runtime value here (a floor number, a
// player's price) and every distinct value becomes its own permanent SLOT,
// straight into the
// 250 cap. tools/lint_tod_hints.js fails the build on a variable hint that has
// not declared its bound, which is the guard for exactly this.
// (The old wording also relied on "[cost:" being harmless on a HINT_NOICON
// trigger because the wallbuy router "needs [cost:] AND an icon". That premise
// was FALSE — the icon guard never fired, and this crate drew the "Wall Weapon"
// card in game for months. Fixed in the router; not relied on here either way.)
function crate_hint()
{
	return ( "Hold ^3[{+activate}]^7 ^5AMMO CRATE^7 - Regular ^2$" + TOD_CRATE_COST_BASE
	         + "^7 / Pack a Punch ^2$" + TOD_CRATE_COST_PAP );
}

// The crate MODEL. Returns undefined if the entity pool is full — every caller
// must cope (a missing crate is buyable elsewhere). Not solid: the collision is a generator-cut clip
// brush inside the mesh, for EVERY crate (v17.38) — see the header.
function spawn_model( org, yaw )
{
	m = Spawn( "script_model", org );
	if ( !isdefined( m ) )
		return undefined;
	m.angles = ( 0, yaw, 0 );
	m SetModel( "tod_ammo_chest" );   // the Ammo Box V6 (docs/208): front = model +Y = yaw + 90, built to crateBox
	return m;
}

// -> the crate's FRONT as a unit vector (front = yaw + 90; see the placement
// note above). Yaw only — a crate never pitches.
function crate_front( yaw )
{
	return AnglesToForward( ( 0, yaw + 90, 0 ) );
}

// -> where this crate's trigger goes: crate_trig_out() in front of the origin,
// lifted. One function so no two crates can ever place it two ways.
function trig_org_for( org, yaw )
{
	return org + VectorScale( crate_front( yaw ), tod_breather_data::crate_trig_out() ) + ( 0, 0, TOD_CRATE_TRIG_LIFT );
}

// The crate USE TRIGGER, already threaded on the shared use_loop. Takes the yaw
// because the trigger stands IN FRONT of the crate (see the define block).
function spawn_trigger( org, yaw )
{
	t = Spawn( "trigger_radius_use", trig_org_for( org, yaw ), 0, tod_breather_data::crate_trig_r(), TOD_CRATE_TRIG_H );
	if ( !isdefined( t ) )
		return undefined;
	t TriggerIgnoreTeam();      // REQUIRED for a script-spawned use-trigger
	t SetCursorHint( "HINT_NOICON" );
	t SetHintString( crate_hint() );
	t thread use_loop();
	return t;
}

function place( org, yaw )
{
	m = spawn_model( org, yaw );
	spawn_trigger( org, yaw );
	return m;
}

// (crate_clips() lived here from v13.9 to v17.38 — three zm_collision_perks1
// colliders spread along AnglesToRight, which at a crate's yaw is its FRONT
// axis, so the row ran front-to-back and planted an invisible lip beyond the
// face. Every crate now has a generator-cut box rotated to its own yaw.)

// self = the trigger
function use_loop()
{
	// self endon( "death" ) — MAP 1 HAS IT AND WE DID NOT (v14.58, found by the
	// map-wide prompt audit). It is invisible for the static crates, whose
	// triggers are never deleted (it mattered for the retired spire, which
	// deleted crate triggers as players climbed). Cheap insurance for any future
	// deleted trigger, and it costs the static crates nothing.
	self endon( "death" );
	level endon( "end_game" );

	for ( ;; )
	{
		self waittill( "trigger", player );

		if ( !isdefined( player ) || !isplayer( player ) )
			continue;
		if ( !zm_utility::is_player_valid( player ) )
			continue;                       // downed / spectating
		if ( player laststand::player_is_in_laststand() )
			continue;
		// A revive press is not a purchase (_zm_blockers.gsc:307). Reviving polls
		// the raw USE button (_zm_laststand.gsc:1129), so without this the press
		// that revives a teammate also charges for a refill. Silent, like the
		// branch above: the player is holding use.
		if ( player zm_utility::in_revive_trigger() )
			continue;
		// World frozen for an upgrade pick — refuse, but SAY SO. A mute refusal
		// is indistinguishable from a dead trigger (the same silence made a
		// teleporter read as broken on 2026-08-26; see the long note at
		// _tod_teleport.gsc's copy of this branch). The window is up to ~20s
		// every fourth round, and a player who already locked their card — or
		// who was down/dead and sat the event out — is unfrozen and walking
		// around inside it. Every other refusal in this loop already sounds.
		if ( IS_TRUE( level.tod_upgrade_pause ) )
		{
			player PlaySound( "zmb_no_purchase" );
			continue;
		}

		weapon = player GetCurrentWeapon();

		// NOTHING TO REFILL -> refuse and charge NOTHING. Taking 5000 points
		// for a no-op is the worst thing this trigger could do, so the melee
		// gate comes before the wallet check. The blades are the slasher's
		// whole ladder plus the bowie alt (see _tod_classes::register_melee_dmg
		// — keep the stems in step with that list).
		if ( !has_ammo( weapon ) )
		{
			player PlaySound( "zmb_no_purchase" );
			continue;
		}

		// ALREADY FULL -> REFUSE, AND CHARGE NOTHING (audit 2026-08-25).
		// GiveMaxAmmo on a full reserve is a no-op, so the crate happily took
		// 5,000 points and did nothing. Easiest to hit right after a Max Ammo
		// drop — which is exactly when a player is most likely to walk past it.
		// Ordered BEFORE the wallet check for the same reason the melee gate is:
		// taking points for nothing is the worst thing this trigger can do.
		if ( player GetWeaponAmmoStock( weapon ) >= weapon.maxAmmo )
		{
			player PlaySound( "zmb_no_purchase" );
			continue;
		}

		// v13.23 two-tier: the held weapon's PaP state picks the price.
		//
		// TWO CHECKS, NOT ONE (2026-08-30, live report: a PaP'd gun bought
		// crown-crate ammo at the 2500 base price). The old comment claimed
		// "the class-gun _up twins ARE upgraded forms, so is_weapon_upgraded
		// covers them natively" — WRONG for part of the roster.
		// is_weapon_upgraded answers from level.zombie_weapons_upgraded, which
		// is loaded from zm_levelcommon_weapons.csv — and that CSV's rows for
		// the _zm-SUFFIXED twin families (the Enfield ladder, the knives,
		// leviathan) name the forms WITHOUT the _zm suffix the shipped assets
		// carry, so the table rows point at weapons that don't exist and a
		// held t5_enfield_up_*_zm reads as not-upgraded. The name check covers
		// every generated PaP form ("_up" / "_up_*"), the stock "_upgraded"
		// forms (MR6), and can't drift when the generator grows a new family;
		// the stock check stays for anything named differently. (The ~1s
		// pre-reconcile window after a tier card remains the one edge, and it
		// under-charges rather than over-charges.)
		cost = TOD_CRATE_COST_BASE;
		if ( zm_weapons::is_weapon_upgraded( weapon ) || IsSubStr( weapon.name, "_up" ) )
			cost = TOD_CRATE_COST_PAP;

		if ( !( player zm_score::can_player_purchase( cost ) ) )
		{
			player PlaySound( "zmb_no_purchase" );
			continue;
		}

		player zm_score::minus_to_player_score( cost );
		player PlaySound( "zmb_cha_ching" );
		// Fills the shared RESERVE; the magazine tops off on the next reload,
		// exactly like the stock Max Ammo powerup.
		player GiveMaxAmmo( weapon );
		wait 0.75;                          // debounce a held [activate]
	}
}

// -> true if `weapon` is something GiveMaxAmmo can meaningfully fill.
// The map's melee weapons carry no reserve, so a refill would be a silent
// no-op the player paid 5000 for.
function has_ammo( weapon )
{
	if ( !isdefined( weapon ) || weapon == level.weaponNone )
		return false;
	if ( !isdefined( weapon.name ) )
		return false;

	if ( IsSubStr( weapon.name, "cc_punch" ) || IsSubStr( weapon.name, "cc_gauntlet" ) || IsSubStr( weapon.name, "cc_gold_sword" ) )   // 2026-09-26: punch / gauntlet / sword
		return false;

	// The bowie alt (the retired bat / wakizashi / Stormbreaker exemptions left with the Map 1 purge).
	if ( IsSubStr( weapon.name, "bowie" ) )
		return false;

	return true;
}
