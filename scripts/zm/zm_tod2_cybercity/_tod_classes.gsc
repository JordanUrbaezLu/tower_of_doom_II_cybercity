// =============================================================================
// _tod_classes.gsc â€” the class system: 4 classes x 3 TIERS of guns.
//
// CLASS TIERS (docs/25, user 2026-08-22): a class is an identity (move speed,
// the draft, the domain pool gate); what the player HOLDS is the gun of their
// current TIER (player.tod_tier, 1..3). A TIER card (dealt by _tod_upgrades
// once the class gun is PaP'd) promotes the tier: a new gun (unpacked), GUN-scoped
// upgrades reset, CLASS-scoped ones kept. Since 2026-09-27 NO live card is
// gun-scoped (_tod_upgrades set_scope), so a promotion keeps every card.
//
// Every module resolves "the class gun" PER PLAYER through gun( player ) â€”
// never through a class-level primary (that coupling is what tiers broke).
//
// LADDERS (user 2026-08-22):
//   SKIRMISHER  MSMC        -> MP5        -> MP7
//   ASSAULT     Enfield       -> Krig 6     -> AK-47
//   HEAVY       Mk 48     -> HK21       -> Death Machine
//   SLASHER     Combat Knife  -> Katana     -> STORMBREAKER (the Leviathan port)
// PHASE 1 (this file) ships the NULL LADDER â€” every tier is today's T1 gun â€”
// which proves the card / reset / swap / latch flow with ZERO new assets.
// Phase 2 swaps the stems in ONE GUN PER BUILD (docs/25 Â§7, Â§11).
//
// SCALABILITY DOCTRINE (the "no twin matrix" answer, see _tod_upgrades.gsc):
// a gun costs its generated variant forms only (base tune x ladder x base/_up);
// every upgrade the tower grants is SCRIPT-side state. Map 1 measured the
// engine's registration ceiling (~230 safe, silent 0xC0000005 boot AV past
// it, docs/21 Â§A) â€” tools/gen_tod_twins.js prints the ledger and throws > 200.
//
// Adding a gun (docs/25 Â§7, condensed): screen the GDT for a live altWeapon
// (boot trap), add it to gen_tod_twins.js (variants + zone + CSV rows) and
// gen_tod_sounds.js, then ONE register_gun line here. Boot-test after EVERY
// gun added â€” never batch (map 1's hard rule).
// =============================================================================

#using scripts\shared\callbacks_shared;
#using scripts\shared\flag_shared;
#using scripts\zm\_zm_utility;    // include_weapon (PaP table repair)
#using scripts\zm\_zm_weapons;    // add_zombie_weapon (PaP table repair)
#using scripts\shared\util_shared;
#using scripts\zm\_zm_utility;
#using scripts\shared\laststand_shared;   // camo_watch's crawl guard â€” IsAlive is
                                          // TRUE in last stand, so it proves nothing

#insert scripts\shared\shared.gsh;

#define TOD_TIER_MAX        3
// [TOD_BREACHER] (docs/157): one console line per Breacher gun hand-out (draft,
// promotion, PaP, re-dress) - the weapon form, its ammo after the give and the
// camo index. Its OWN switch, not tod_dev, so the user's dev-off playtest still
// records it (their launcher passes developer 1 + devblock). A give is a rare
// event; nothing here touches gameplay. Zero before a publish.
#define TOD_BREACHER_LOG    1

// =============================================================================
// PACK-A-PUNCH TIERS (v17.33, user 2026-09-04: "add triple pack but give the
// same weapon back ... under the hood we increase the damage rather than
// having a twin").
//
// WHY IT CANNOT BE A WEAPON VARIANT, in one number: tools/gen_tod_twins.js
// prints REGISTRATION LEDGER 201 generated + 28 fixed = 229 against a guard of
// 229. There is ZERO headroom. A packed-again form of every ladder rung is not
// expensive here, it is impossible â€” the generator throws and writes nothing.
// So the tier is SCRIPT STATE and the damage is arithmetic in the one damage
// callback, which is the same NO-TWIN doctrine the map already runs for
// damage / fire rate / mag size.
//
// TIER 1 IS "PACKED", and it is derived, never stored: the existing packed
// test (tod_pap_owned for the class primary, the "_up" name test / stock's
// is_weapon_upgraded for anything else) already answers it, and a second store
// for a fact that already has one authority is how the two drift apart.
// Tiers 2 and 3 were sold only by the retired spire's machines; nothing
// writes them now.
//
// KEYED BY STEM, NOT BY WEAPON NAME. The class primary's asset name walks the
// twin ladder every time a gun-scoped domain levels (cc_fire_bow_up_r1m2 -> _r1m3)
// and gains/loses "_up" at the pack, so a name key would silently drop the
// tier on the next upgrade card. pap_stem() folds every one of those forms
// onto the registered g.stem. A TIER PROMOTION changes the stem by design â€”
// it is a different gun, and it arrives at tier 0 with everything else reset.
// =============================================================================
#define TOD_PAP_TIER_MAX    3
// +50% of the packed gun's damage per tier above 1 (user: "+50% damage at each
// level", ADDITIVE by their call: II = x1.5, III = x2.0 â€” not x1.5 compounded).
// The multiplier is applied to the RAW damage beside gun_balance_mult, so it
// scales the base hit and every damage domain together instead of competing
// with a maxed DAMAGE domain inside the additive sum.
#define TOD_PAP_TIER_ADD    0.50

// A GUN'S FIRST PACK IS ITS _up ASSET, and that asset is where the reward
// lives: the generator bakes +25% damage and -20% fireTime into every _up
// twin, which is x1.5625 on damage per second. pap_tier_mult() therefore
// returns 1.0 at tier 1 for a gun and is CORRECT to -- the twin already paid.

// =============================================================================
// PACK-A-PUNCH CAMO (v17.35, 2026-09-04) â€” the camo index each tier wears.
//
// THIS MAP HAS NEVER SHOWN A PaP CAMO, and not because nobody set the index:
// stock's give_build_kit_weapon has always passed level.pack_a_punch_camo_index
// (42) and every _up variant carries a camo table. The break was one layer down.
// The tables name their materials as strings and the mod tools ship no GDT for
// the stock ones, so each lands in the .ff as a NAME-ONLY STUB: 20-29 bytes,
// the same shape as the known-missing mtl_glass (14 B), against 1146 B for one
// of ours â€” and not one i_t7_camo_* texture ships. Every stock index is
// therefore a no-op here. (Read the RECORD SIZES in assetinfo, not the presence
// of the name: the names are all there.)
// tools/gen_tod_camo.js now bakes three camos we own; gen_tod_twins.js points
// every _up form at a per-gun table whose slots are OUR materials.
//
// The numbers below are SLOTS IN THAT GENERATED TABLE, not stock camo indices:
//     1 GRID      cyan on navy    tier I  â€” the ordinary 5,000 pack
//     2 CIRCUIT   magenta traces  tier II â€” the spire's 25,000
//     3 OVERLOAD  gold over red   tier IIIâ€” the spire's 50,000
//     4 (control) mtl_origins_camo_alt, a camo PROVEN to render in this build
//
// SLOT 4 IS THE DIAGNOSTIC. If the tiers come back blank in game, point
// TOD_PAP_CAMO_T1 at 4 and rebuild: a camo on slot 4 and nothing on 1-3 means
// our materials are wrong; nothing on either means the give lane never applied
// options at all. One build tells them apart â€” that is the whole reason the
// slot exists, and it costs nothing to keep.
//
// A gun the generator could not build a table for keeps what it had, which is
// no camo â€” never a white square, because the fallback is the model's own
// materials.
// =============================================================================
// =============================================================================
// v17.50 (2026-09-04) â€” THE TIERS WEAR STOCK CAMOS FROM THE PORTS' OWN TABLES.
//
// Everything above this line about stub materials is WRONG and is kept as the
// record of a theory that cost four builds. The v17.48 control (every _up twin
// on its port's own table, every packed gun asking for slot 28) RENDERED â€”
// user: "tier 1 works" â€” so the mechanism fires on the twins and the stock
// materials the linker records as 20-byte references ARE resolved at runtime
// from the base game. What never drew was our three custom materials
// (tod_camo_pap1..3, gen_tod_camo.js): three builds of art, alpha, layers and
// semantics, and not one pixel. Their recipe is unknown; the stock slots are
// proven, so the tiers ride them.
//
// The numbers are SLOTS IN THE SHIP TABLE every Skye pack ships (75 slots,
// baseIndex 1, the same layout on t5/t6/t8/t9/iw7 and the melee tables â€”
// verified across the install before choosing):
//     28  mtl_t7_camo_ce_115       PACK I    Element 115 â€” the slot the
//                                            control rendered on
//     42  mtl_wpn_t7_camo_etching  PACK II   the Der Riese etching, stock
//                                            zombies' own PaP camo
//     22  mtl_wpn_t7_camo_gold     PACK III  gold â€” the crown's colour
// A slot that comes back blank on some pack is that pack's table missing the
// material, never the lane: swap the number, nothing else.
//
// gen_tod_twins.js keeps CAMO_KEEP_PORT_TABLE = true for this: the `_up`
// twins keep the port's `camo` field. The tod_camo_* tables it still emits
// are unreferenced (drop them with CAMO_ENABLED = false at the next FULL
// build â€” GDT).
// =============================================================================
// v17.53 (user 2026-09-04, after playing 28/42/22: "I like gold as 1st,
// element 115 as 2nd or 3rd but we need a sick new one. Der riese was
// horrible"): gold leads, 115 is the middle, and the top tier is DARK MATTER
// (slot 8, mtl_wpn_t7_camo_darkmater_epic â€” BO3's animated prestige camo).
// Alternates if 8 comes back blank or wrong for the map: 29 cyborg, 62
// integer emissive, 40 red anodized hex. The full 75-slot menu is in the
// ship table of any Skye pack (skye_t9_mac-10.gdt, "t9_camo_mac10_ship").
// v17.57 FINAL (user 2026-09-04, after seeing 29/62/40 in play: "Lets do gold,
// red hex, 115"): gold for the ordinary pack, red anodized hex for PACK II,
// Element 115 for PACK III. All three PLAY-PROVEN on these tables that night.
// Slot 8 (the table's "dark matter") rendered desert-orange â€” trust eyes over
// names; the dev crouch browser below is how to look at any other slot.
// v17.63 (user 2026-09-05: "We will do gold, lucid emssive, and revalations 3 as
// pap camos") — the tiers as chosen off the camo-menu audit.
//     22   mtl_t7_camo_...gold          PACK I    play-proven since v17.57
//     126  mtl_t7_camo_loot_lucid_emissive   PACK II   the spire's 25,000
//     123  mtl_t7_camo_pap_dlc4_03      PACK III  Revelations PaP, variant 3
// The camo table is FIVE blocks (baseIndex 1/76/121/128/136), not one list of 75,
// and 123/126 come out of the half this map had never asked for — index -> material
// is identical on all 167 camo tables in the install from 1 to 126, blades and the
// Stormbreaker included, so one define is one camo on every gun. 127+ is NOT
// (the axe's third sub-table runs its own list from there); never define above 126.
// ⚠️ TABLE SHAPE IS NOT PROOF OF RENDERING. Nothing above 75 has been seen in game
// yet, and a material that does not resolve leaves the weapon in its base
// materials — a packed gun that looks unpacked. PACK I is proven, so the first
// tier that would show it was the retired spire's 25,000; the widened dev camo browser
// below reaches every one of these in about 90 seconds if it needs settling fast.
// v17.91 (user 2026-09-05: "We need to go Lucid, Revalations, Neon City"): gold is
// retired; the ladder is now
//     126  mtl_t7_camo_loot_lucid_emissive   PACK I    (play-proven as the old PACK II)
//     123  mtl_t7_camo_pap_dlc4_03           PACK II   Revelations PaP 3 (play-proven as the old PACK III)
//     124  tod_camo_pap3 — NEON CITY, OURS   PACK III  docs/112. Index 124 is the
//          Revelations-4 slot; gen_tod_twins.js (CAMO_PAP3_INDEX, LOCKSTEP with the
//          define below) copies each port's table and points that one row at our
//          material, so 124 = our camo on every gun that got a copy and Revelations 4
//          on the two knives / the Stormbreaker, which kept their port tables.
//          Index 122 on the copies is the MadGaz CONTROL for the custom-camo test.
#define TOD_PAP_CAMO_T1     126
#define TOD_PAP_CAMO_T2     123
#define TOD_PAP_CAMO_T3     124

// PER-CLASS SECONDARIES (user 2026-08-23: "we need to look into secondarys now
// ... I think we give the knife an automatic pistol CW APM63. The current
// pistol will go to the LMG class. The CW MAGNUM will go to the Assault class.
// For SMG we can give it weakend version of the Ghosts Bulldog").
// Was ONE global TOD_CLASS_SECONDARY "pistol_standard" for every class.
//
// EXPLICITLY NO TWINS (user: "They will all have PaP versions but thats about
// it") â€” each is base + its PaP form and nothing else, so none of these go
// through gen_tod_twins.js and none carry a variant ladder. 6 registrations,
// taking the ledger 159 -> 165 against the 200 guard.
//
// TWO NAME CORRECTIONS, both verified against the installed GDTs:
//   * the CW machine pistol is the AMP63, not "APM63"  -> t9_amp63
//   * the only Bulldog installed is the ADVANCED WARFARE port (s1_bulldog),
//     not the Ghosts one. Both are shotguns, so the intent carries.
// The AMP63's PaP asset breaks the port convention â€” it is
// t9_amp63_rdw_up_zm, NOT t9_amp63_up. That is harmless because the weapons
// CSV carries an explicit `upgrade_name` column (field 2), so PaP resolves by
// table lookup rather than by suffix. Do NOT "fix" it by assuming _up.
// AW Bulldog â€” the skirmisher's emergency shotgun. Now the GENERATED variant
// (v10.8, user 2026-08-23: "clip size can double for base and pap bulldog"):
// s1_bulldog_b carries clip 12 / dmg 120 and s1_bulldog_up_b clip 18 / dmg 240,
// emitted by tools/gen_tod_twins.js from skye_s1_bulldog.gdt exactly like every
// other twin. The stock s1_bulldog asset cannot be edited in place, so the buff
// only reaches the player through THIS name â€” pointing back at the bare stem
// silently reverts the whole change. The old Ã—0.5/Ã—0.75 script nerf is gone too
// (damage_mult_for now returns 1.0 for it).
// ---- THE SECONDARY TABLE â€” 12 SIDEARMS, ONE PER (CLASS, TIER) --------------
// (user 2026-08-24: "every tier for every class needs its own secondary ...
// each teir of secondsries will get better just like the primaries do".)
// Was FOUR names, one per class, tier-blind.
//
// GIVE NAME (what GetWeapon is handed) and MATCH STEM (the substring shared by
// that sidearm's base and PaP asset names) are SEPARATE for every row, and they
// have to be. See the v10.8/v10.23 trap that motivated the original four:
//     pistol_standard -> pistol_standard_upgraded    stem contains base
//     t9_amp63        -> t9_amp63_rdw_up             stem contains base
//     s1_bulldog_b    -> s1_bulldog_up_b             stem does NOT
// The generated twins put their variant suffix at the END, so matching on the
// full give name silently stops seeing PACK-A-PUNCHED sidearms â€” and because
// this map deliberately runs with the stock too-many-weapons monitor OFF
// (v9.18: it confiscated class guns), the consequence is walking around holding
// two sidearms in primary slots, not a tidy auto-reap.
//
// EVERY TIER-2 AND TIER-3 NAME IS A GENERATED TWIN (tools/gen_tod_twins.js) and
// carries the "_b" suffix. Pointing any of these at the bare stock stem hands
// out the UN-NORMALIZED port â€” the Klauser ships at damage 20 and the RPG at
// 5250, so that mistake is silent in one direction and catastrophic in the
// other. If a name here and the generator's emitted name ever disagree, the
// class draft hands out a weapon that does not exist.
//
// KEEP THE TWO SWITCHES BELOW IN LOCKSTEP: secondary_name() and
// secondary_stem() are indexed by the same (class, tier) pair and a row added
// to one but not the other fails open (falls through to the heavy T1 pistol).
#define TOD_DEV_ALL_GUNS_POLL 2.0   // dev_all_guns_watch refill period (s)
// 2026-09-28: the twelve TOD_SEC_* give NAMES are retired with the generated sidearms (gen_tod_twins
// enabled:false on all ten; no class has carried a secondary since build 5, secondary_name() answers "").
// The TOD_SECSTEM_* reap stems below stay: a save/respawn can still find an old sidearm to take away.

// MATCH STEMS, in lockstep with the twelve names above.
// t6_executioner is the one stem that must catch THREE assets, not two: its PaP
// form is dual wield, so t6_executioner_rdw_up_b (the half the player fires) and
// the stock t6_executioner_ldw_up_zm both have to be reaped on a class switch.
// The bare stem covers all three, which is exactly why this is a stem and not a
// name.
#define TOD_SECSTEM_NECROMANCER_1 "s1_bulldog"
#define TOD_SECSTEM_NECROMANCER_2 "t8_sg12"
#define TOD_SECSTEM_NECROMANCER_3 "t6_spas12"
#define TOD_SECSTEM_ASSAULT_1    "t9_magnum"
#define TOD_SECSTEM_ASSAULT_2    "t8_mog12"
#define TOD_SECSTEM_ASSAULT_3    "t6_executioner"
#define TOD_SECSTEM_HEAVY_1      "pistol_standard"
#define TOD_SECSTEM_HEAVY_2      "t6_rpg"
#define TOD_SECSTEM_HEAVY_3      "t9_nail_gun"
#define TOD_SECSTEM_SLASHER_1    "t9_amp63"
#define TOD_SECSTEM_SLASHER_2    "iw7_udm"
#define TOD_SECSTEM_SLASHER_3    "t8_rk7"
// Stock's Easter-egg reward gun (level.super_ee_weapon, the RK5). Not a class sidearm;
// take_foreign_secondaries always reaps it (map 1's v19.55, ported 2026-10-04).
#define TOD_RK5_STEM             "pistol_burst"

#namespace tod_classes;

function init()
{
	level.tod_classes = [];
	level.tod_class_count = 0;
	// Registration ORDER = the class id the draft (_tod_class_select::class_key,
	// tod_class_select.lua) and the TIER card's class code use: 1 SKIRMISHER /
	// 2 ASSAULT / 3 HEAVY / 4 SLASHER. Never reorder.
	// 2026-09-26 (user): THE NECROMANCER replaces the SKIRMISHER in slot 1 - the
	// "skirmisher" key is retired everywhere; id 1 does not move.
	register_class( "necromancer", "NECROMANCER", ( -390, -280, 0 ) );
	register_class( "assault",    "ARCHER",    ( -280, -280, 0 ) );
	register_class( "heavy",      "BREACHER",   ( -170, -280, 0 ) );   // TOD II (docs/157): the Hellbound BREACHER's name; the key stays "heavy" so every id, domain and table keyed on it holds
	register_class( "slasher",    "WARRIOR",    (  -60, -280, 0 ) );

	// PaP table repair â€” see repair_weapon_table(). Threaded, waits for the
	// blackscreen flag so stock's weapons table is fully built first.
	level thread repair_weapon_table();

	// ---- TIER LADDERS â€” PHASE 1 NULL LADDER (every tier = the T1 gun) -------
	// register_gun( class, tier, stem, pap suffix, variant axes, alt weapon, grant )
	//   stem     the runtime asset stem; variants are stem[+pap][+suffix]
	//            (asset ids may carry a trailing _zm the engine strips â€” the
	//            knife does; runtime names are bare, so stems never carry it)
	//   axes     the gun's generated twin ladder(s) -> the variant suffix
	//            (_f1h2 / _r0m3 / _p1 / _k4); undefined = a single base form "_b"
	//   alt      an extra weapon given with the gun (the slasher's bowie)
	//   grant    a domain key set to Lv1 the moment the gun arrives by tier-up
	//            (the Stormbreaker arrives with THOR'S THUNDER) â€” Phase 2
	// SMG CLASS UPDATE (user 2026-08-23, v9.44): FIRE RATE (f) is the MSMC's
	// alone, HANDLING (h) is every SMG, MAG SIZE (m) left the class. Axis
	// letters + ORDER mirror gen_tod_twins.js LADDER.skirmisher exactly â€” the
	// variant suffix is composed from this list (_f1h2 / _h3).
	// TOWER OF DOOM II (2026-09-20, docs/153): the Hellbound skirmisher ladder
	// Saug -> M1927 -> C.A.R. under this map's cc_* stems (gen_tod_twins.js
	// LADDER.skirmisher explains the naming and the DPS pin). Axes unchanged.
	// THE NECROMANCER (2026-09-26): the Skull of Nan Sapwe (Zetsubou's skull,
	// source_data/tod_necro_skull.gdt via tools/necromancer/make_skull_gdt.py).
	// Hold FIRE = the soul beam (drains and kills), hold AIM = summon helpers
	// (_tod_necro_skull.gsc + _tod_necro_summon.gsc). ONE form ("_b") + its PaP.
	// Tier 2/3 use new skull staffs with the native ice-staff grip/cast set.
	// Tier and PaP mechanics remain owned by the existing class progression.
	register_gun( "necromancer", 1, "tod_necro_skull",     "_up", undefined,                               undefined,     undefined );
	register_gun( "necromancer", 2, "tod_necro_staff2",     "_up", undefined,                               undefined,     undefined );
	register_gun( "necromancer", 3, "tod_necro_staff3",     "_up", undefined,                               undefined,     undefined );
	register_gun( "assault",    1, "cc_bow",           "_up", axes2( "deadeye", "d", "shotspeed", "s" ),                   undefined,     undefined );   // Phase 2b: Enfield opens the run
	register_gun( "assault",    2, "cc_crossbow",             "_up", axes2( "deadeye", "d", "shotspeed", "s" ),                    undefined,     undefined );
	register_gun( "assault",    3, "cc_fire_bow",              "_up", axes2( "deadeye", "d", "shotspeed", "s" ),                   undefined,     undefined );   // Phase 2e: the CW AK-47
	// TOD II (2026-09-23, docs/157): the HEAVY is the BREACHER now -
	// Mozambique -> Remington 870 MCS -> Peacekeeper (was Mk 48 -> HK21 ->
	// Death Machine). Axes unchanged: p (PENETRATION) on T1 and T3, T2 one "_b"
	// form. This list, gen_tod_twins.js LADDER.heavy and set_guns( "penetration" )
	// in _tod_upgrades.gsc are three views of ONE fact.
	register_gun( "heavy",      1, "cc_mozambique",        "_up", axes1( "pellets", "e" ),                  undefined,     undefined );   // TOD II: Apex Mozambique (was t6_mk48)
	register_gun( "heavy",      2, "cc_rem870",            "_up", axes1( "pellets", "e" ),                  undefined,     undefined );   // TOD II: BO2 Remington 870 MCS (was t5_hk21)
	register_gun( "heavy",      3, "cc_peacekeeper",       "_up", axes1( "pellets", "e" ),                  undefined,     undefined );   // TOD II: Apex Peacekeeper; PaP = the mythic Breach SWAT (was t6_death_machine)
	register_gun( "slasher",    1, "cc_punch",            "_up", axes1( "knifespeed", "k" ),               "bowie_knife", undefined );   // 2026-09-26: ONE INCH PUNCH (Origins; was cc_twin_knives). source_data/tod_warrior_punch.gdt
	register_gun( "slasher",    2, "cc_gauntlet",         "_up", axes1( "knifespeed", "k" ),               "bowie_knife", undefined );   // 2026-09-26: GAUNTLET OF SIEGFRIED (Gorod Krovi's Dragon Gauntlet, melee half; was cc_plain_sword)
	register_gun( "slasher",    3, "cc_gold_sword",            "_up", axes1( "knifespeed", "k" ),               "bowie_knife", undefined );   // Gold Battle Sword. The THOR'S THUNDER Lv1 grant that rode here was retired 2026-09-26 with the card (Warrior card cut)

	// ---- ASSET TAILS (2026-08-23) -----------------------------------------
	// Some ports name their generated forms with a TRAILING "_zm" AFTER the
	// ladder suffix, and it is not consistent between a gun's base and PaP
	// forms. The generator (gen_tod_twins.js LADDER[].forms[].name) is the
	// source of truth; these three lines mirror it, and variant_name() below is
	// the ONLY place that assembles a name from the parts.
	//
	// WHAT THIS BUG COST (user 2026-08-23: "why couldnt i pap my enfield"): the
	// script built "cc_twin_knives_k3" while the asset is
	// "cc_twin_knives_k3_zm", so GetWeapon returned weaponNone and
	// reconcile_twin took its "variant not linked" early-out. Silently. That
	// meant KNIFE SPEED never moved a blade on ANY of the three slasher guns,
	// and a PaP'd Enfield could not walk its recoil/mag ladder either â€” no
	// error, no log line, the upgrade just did nothing.
	//
	// If a NEW gun is added, check its forms[].name in the generator and add a
	// line here when either form carries a tail. The generator's csv/zone
	// cross-check catches the CSV half of this class of bug; this is the GSC half.
	// NO set_tails CALLS. This was briefly wrong in the other direction on
	// 2026-08-23 and it BROKE THE KNIFE, so the evidence is written down here:
	//
	//   THE ENGINE STRIPS A TRAILING "_zm" FROM A WEAPON ASSET NAME.
	//   The script name is the asset name WITHOUT it.
	//
	// Proof, three independent shipped sources:
	//   * map 1 zones ONLY "cc_gold_sword_zm" / "cc_gold_sword_up_zm" and its weapons
	//     CSV says "cc_gold_sword,cc_gold_sword_up" â€” and map 1's Leviathan works.
	//   * map 1 zones ONLY "freezegun_zm" / "freezegun_upgraded_zm"; CSV says
	//     "freezegun,freezegun_upgraded".
	//   * THIS map: the asset is "t9_amp63_rdw_up_zm" and the hand-authored CSV
	//     row is "t9_amp63,t9_amp63_rdw_up" â€” note "_rdw" is KEPT and only
	//     "_zm" is dropped, so it is that exact suffix and not a general rule.
	// And the live one: the slasher has been carrying a working blade the whole
	// time while the script asked GetWeapon for "<stem>_k0" against an asset
	// named "<stem>_k0_zm".
	//
	// So variant_name() returns the BARE name, weapon_or_zm() below tries the
	// "_zm" form as a fallback anyway (cheap, and it removes the guess), and the
	// generator strips "_zm" when it writes the weapons CSV.

	// MELEE DAMAGE PER BLADE (docs/25 Â§6 MELEE_TIER_DMG â€” the generator bakes
	// the same numbers into the assets; this table is the script-side mirror,
	// because weapon objects do not expose meleeDamage to script). [base, PaP]
	//
	// CURRENTLY UNCONSUMED (2026-08-24): melee_dmg() below had exactly one
	// caller â€” CHAIN LUNGE's DoDamage â€” and that module was removed. The table
	// is kept because it is the readable mirror of the generator's numbers and
	// the hook any future script-side melee hit will need. If nothing has
	// consumed it by the next melee pass, DELETE it rather than let two copies
	// of one number drift apart (this repo has already paid for that once, in
	// _tod_bosses.gsc's hand-copied upgrade constants).
	level.tod_melee_dmg = [];
	// MELEE LADDER (user 2026-08-23: "they are scaling way too high... once you
	// get the katana you can one hit rest of game... I see 20k which is crazy").
	// MUST STAY IN LOCKSTEP with MELEE_TIER_DMG in tools/gen_tod_twins.js â€” the
	// GSC value drives any script-side DoDamage, the generator value drives the
	// asset's meleeDamage. They are two copies of one number.
	//
	// The old ladder was 1700/20000, 20000/40000, 40000/80000. Its real flaw
	// was not the top end but the FIRST STEP: the knife's PaP was a x11.8 jump
	// (1700 -> 20000) while every other step doubled, so a PaP'd TIER-1 knife
	// already hit as hard as the katana â€” 20000 one-hits to round 38, or round
	// 54 with the DAMAGE domain maxed. That is the whole game, which is exactly
	// what the user reported.
	//
	// Now a clean x2 ladder that mirrors the GUN rule (tier N base = tier N-1
	// PaP). Against this map's zombie HP (stock curve x TOD_ZHEALTH_MULT 1.25:
	// r20 ~3.4k, r30 ~8.8k, r40 ~22.8k) the one-hit reach is:
	//   knife  2000 -> r14   PaP  4000 -> r21
	//   katana 4000 -> r21   PaP  8000 -> r29
	//   storm  6800 -> r28   PaP 13600 -> r35   (r43 with DAMAGE 10)
	// STORMBREAKER -15% (user 2026-08-24: "Storm breaker needs an all around
	// nerf by like 15%") â€” 8000/16000 -> 6800/13600. It is the one rung that now
	// breaks "tier N base = tier N-1 PaP": a PaP'd katana (8000) out-hits a fresh
	// axe (6800) until the axe is PaP'd. ~1 round of one-hit reach, accepted as
	// the direct cost of nerfing the top rung on its own.
	// So every tier buys ~7-8 more rounds of one-hitting and melee stops being
	// a free win around r36 â€” strong, never permanent.
	// MELEE -20%, EVERY RUNG (user 2026-08-30: "nerf damage on melee by 20%").
	// Base and PaP alike, so the ladder shape above is intact and only its
	// height moves; one-hit reach slides ~2 rounds earlier per rung (PaP storm
	// r35 -> ~r33). Backstab is DERIVED in the generator (x1.5), so it follows.
	register_melee_dmg( "cc_punch",            1600, 3200 );   // 2026-09-26: the One Inch Punch took the knives' rung
	register_melee_dmg( "cc_gauntlet",         3200, 6400 );   // 2026-09-26: the Gauntlet of Siegfried took the sword's rung
	register_melee_dmg( "cc_gold_sword",            5440, 10880 );  // -15% 2026-08-24, then -20% 2026-08-30

	check_stem_prefixes();

	callback::on_spawned( &on_player_spawned );

	// Class-switch STATIONS REMOVED (user 2026-08-20: "you are not able to
	// switch class once game has started"). The game-start draft assigns the
	// class permanently.
}

function register_class( key, display, station_org, draftable )
{
	c = SpawnStruct();
	c.key = key;
	c.display = display;
	c.station_org = station_org;   // vestigial (stations removed 2026-08-20), harmless
	c.tiers = [];
	// DRAFTABLE (2026-09-07) -- may random_class_key() hand this class to a
	// drop-in joiner? DEFAULTS TRUE, so the four 3-arg calls in init() are
	// unchanged (GSC pads a missing arg with undefined, and lint_tod_arity only
	// fails on TOO MANY args). It exists because REGISTERED and DRAFTABLE are
	// two different questions and this map only ever asked one: a class
	// registered for a dev run must not be able to arrive by the hot-join lane.
	c.draftable = ( ( isdefined( draftable ) ) ? draftable : true );
	level.tod_class_count++;
	c.id = level.tod_class_count;  // 1..N, registration order (see init)
	level.tod_classes[ key ] = c;
}

function register_gun( class_key, tier, stem, up_suffix, axes, alt, grant )
{
	g = SpawnStruct();
	g.class_key = class_key;
	g.tier = tier;
	g.stem = stem;
	g.up_suffix = up_suffix;   // the port's PaP form suffix ("_up" skye / "_upgraded" stock-style)
	g.axes = axes;             // array of { domain, letter } or undefined
	g.alt = alt;               // extra class weapon (slasher's bowie) or undefined
	g.grant = grant;           // domain key granted at Lv1 on arrival, or undefined
	level.tod_classes[ class_key ].tiers[ tier ] = g;
	if ( IS_TRUE( level.tod_dev ) )
	{
		msg = "[TOD_ROSTER] REGISTER class=" + class_key + " tier=" + tier + " stem=" + stem + " pap=" + up_suffix;
		/# PrintLn( msg ); #/
	}
}

function register_melee_dmg( stem, base, up )
{
	m = SpawnStruct();
	m.stem = stem;
	m.base = base;
	m.up = up;
	level.tod_melee_dmg[ level.tod_melee_dmg.size ] = m;
}

// PUBLIC â€” the melee damage the held blade deals (base or PaP form by name).
// Unknown blade -> the knife's PaP value (the pre-tier behaviour).
function melee_dmg( weapon )
{
	if ( isdefined( weapon ) && isdefined( weapon.name ) && isdefined( level.tod_melee_dmg ) )
	{
		for ( i = 0; i < level.tod_melee_dmg.size; i++ )
		{
			m = level.tod_melee_dmg[ i ];
			if ( !IsSubStr( weapon.name, m.stem ) )
				continue;
			if ( IsSubStr( weapon.name, "_up" ) )
				return m.up;
			return m.base;
		}
	}
	// Unknown blade -> the KNIFE'S BASE. Was 20000 (the old knife-PaP value),
	// which after the 2026-08-23 retune would have made any unrecognised blade
	// hit 5x harder than the top-tier Stormbreaker's base. A fallback should be
	// the floor of the ladder, never above its ceiling.
	return 2000;
}

// PUBLIC â€” THE one place a variant asset name is assembled. Every caller that
// used to concatenate stem + up_suffix + suffix by hand must come through here,
// or the tails above are silently dropped again.
function variant_name( g, is_up, suffix )
{
	if ( !isdefined( g ) )
		return "";
	n = g.stem;
	if ( is_up )
		n += g.up_suffix;
	return n + suffix;
}

// ===========================================================================
// PACK-A-PUNCH TIERS â€” the store. See the define block at the top of the file
// for why this is script state and not a weapon asset.
// ===========================================================================

// PUBLIC â€” the stable per-gun key. Every form of one gun (base, packed, and
// every rung of the twin ladder) folds onto ONE string, so levelling a
// gun-scoped domain cannot drop a tier the player paid 50,000 for.
//
// The class roster answers by its REGISTERED stem â€” gun() for the primary and
// secondary_stem() for the sidearm â€” which is the only source that survives
// the ladder. In practice those two ARE every weapon a player can pack in this
// map, so the fallback below is defensive rather than load-bearing: anything
// else is keyed on its own name with the pack suffix cut off, both spellings,
// because this map carries both ("_up" on the Skye ports, "_upgraded" on the
// stock-style ones).
//
// NOT StrTok. StrTok splits on a CHARACTER SET, not a substring, so
// StrTok( n, "_upgraded" ) would break the name at every _, u, p, g, r, a, d
// and e in it. GetSubStr + .size is the shape stock uses for exactly this
// (_zm_weapons.csc:393).
function pap_stem( player, weapon )
{
	if ( !isdefined( weapon ) || !isdefined( weapon.name ) )
		return "";
	n = weapon.name;

	if ( isdefined( player ) )
	{
		foreach ( stem in class_stems( player ) )
		{
			if ( IsSubStr( n, stem ) )
				return stem;
		}
		c = get_class( player );
		if ( isdefined( c ) )
		{
			s = secondary_stem( c.key, tier( player ) );
			if ( isdefined( s ) && s != "" && IsSubStr( n, s ) )
				return s;
		}
	}

	// LONGEST SUFFIX FIRST â€” "_upgraded" starts with "_up", so testing "_up"
	// first would cut "t9_magnum_upgraded" to "t9_magnum" + a stranded tail.
	return pap_strip_tail( pap_strip_tail( n, "_upgraded" ), "_up" );
}

// Cut `tail` off the END of `s` if it is there. Ending-only on purpose: "_up"
// occurs mid-name in this roster's twin forms (cc_fire_bow_up_r1m2) and cutting
// the first occurrence would throw away the ladder suffix that makes the name
// unique â€” harmless for a KEY, but it would also cut a gun whose stem happens
// to contain the letters, which is not.
function pap_strip_tail( s, tail )
{
	if ( !isdefined( s ) || !isdefined( tail ) || s.size <= tail.size )
		return s;
	if ( GetSubStr( s, s.size - tail.size, s.size ) != tail )
		return s;
	return GetSubStr( s, 0, s.size - tail.size );
}

// PUBLIC: 0 = unpacked, 1 = first pack, 2/3 = amplification (sold only by the retired spire).
// Additive primaries store all levels; ordinary guns derive first pack.
function pap_tier( player, weapon )
{
	if ( !isdefined( player ) || !isdefined( weapon ) || !isdefined( weapon.name ) )
		return 0;

	// Additive primaries store every pack level independently, even when
	// their packed and base forms share the same weapon asset.
	if ( pap_independent( player, weapon ) )
	{
		k = pap_stem( player, weapon );
		if ( !isdefined( player.tod_pap_tier ) || !isdefined( player.tod_pap_tier[ k ] ) )
			return 0;
		t = player.tod_pap_tier[ k ];
		if ( t < 0 )
			return 0;
		if ( t > TOD_PAP_TIER_MAX )
			return TOD_PAP_TIER_MAX;
		return t;
	}

	packed = false;
	if ( is_class_primary( player, weapon ) )
		packed = ( IS_TRUE( player.tod_pap_owned ) || IsSubStr( weapon.name, "_up" ) );
	else
		packed = ( IsSubStr( weapon.name, "_up" ) || IsSubStr( weapon.name, "_upgraded" ) );

	if ( !packed )
		return 0;

	if ( !isdefined( player.tod_pap_tier ) )
		return 1;
	k = pap_stem( player, weapon );
	if ( k == "" || !isdefined( player.tod_pap_tier[ k ] ) )
		return 1;
	t = player.tod_pap_tier[ k ];
	if ( t < 1 )
		return 1;
	if ( t > TOD_PAP_TIER_MAX )
		return TOD_PAP_TIER_MAX;
	return t;
}

// Additive loadouts retain each primary, so a shared packed latch cannot apply.
function pap_independent( player, weapon )
{
	c = get_class( player );
	return ( isdefined( c ) && IS_TRUE( c.additive ) && is_class_primary( player, weapon ) );
}

// First-pack authority for machines, pickups and explicit dev grants.
function pap_first_grant( player, weapon )
{
	if ( !is_class_primary( player, weapon ) || pap_tier( player, weapon ) > 0 )
		return;
	if ( pap_independent( player, weapon ) )
		pap_tier_set( player, weapon, 1 );
	else
		player.tod_pap_owned = true;
}

function pap_tier_set( player, weapon, tier )
{
	if ( !isdefined( player ) || !isdefined( weapon ) )
		return;
	k = pap_stem( player, weapon );
	if ( k == "" )
		return;
	if ( !isdefined( player.tod_pap_tier ) )
		player.tod_pap_tier = [];
	player.tod_pap_tier[ k ] = tier;
}

// PUBLIC â€” the damage multiplier the tier is worth. 1.0 at tier 0 and 1, so
// with tiers 2/3 no longer sold the feature is inert, and this call is safe to make
// unconditionally from the damage callback.
function pap_tier_mult( player, weapon )
{
	t = pap_tier( player, weapon );
	if ( t < 1 )
		return 1.0;

	// The first pack is 1.0 here: the _up twin's own GDT already carries it
	// (+25% damage, -20% fireTime; see the PACK-A-PUNCH TIERS block above).
	m = 1.0;

	if ( t < 2 )
		return m;
	return m * ( 1.0 + ( ( t - 1 ) * TOD_PAP_TIER_ADD ) );
}

// PUBLIC - forget ONE stem's stored tier + camo. A same-stem promotion (the
// Necromancer keeps its skull on every tier) must start the new tier unpacked;
// every other class changes stem and never needs this.
function pap_tier_forget( player, stem )
{
	if ( !isdefined( player ) || !isdefined( stem ) ) return;
	if ( isdefined( player.tod_pap_tier ) && isdefined( player.tod_pap_tier[ stem ] ) )
		player.tod_pap_tier[ stem ] = undefined;
	if ( isdefined( player.tod_camo_stamp ) && isdefined( player.tod_camo_stamp[ stem ] ) )
		player.tod_camo_stamp[ stem ] = undefined;
}

// PUBLIC â€” the camo slot this player's copy of `weapon` should wear. 0 = none,
// which is what every UNPACKED gun gets: the camo IS the packed tell, so a base
// gun must never carry one.
function pap_camo_index( player, weapon )
{
	t = pap_tier( player, weapon );
	if ( t <= 0 )
		return 0;

	// (v17.36's slot-4 read and v17.48's slot-28 control lived here; both
	// answered â€” the tiers now ride stock slots, see the defines.)

	// ---- DEV CAMO BROWSER OVERRIDE (v17.54) â€” REMOVE WITH THE DEV HARNESS ----
	if ( IS_TRUE( level.tod_dev ) && isdefined( player.tod_camo_browse ) )
		return player.tod_camo_browse;
	// ---- end dev ---------------------------------------------------------------

	if ( t == 1 )
		return TOD_PAP_CAMO_T1;
	if ( t == 2 )
		return TOD_PAP_CAMO_T2;
	return TOD_PAP_CAMO_T3;
}

// ---- DEV CAMO BROWSER (v17.54, 2026-09-04) â€” REMOVE WITH THE DEV HARNESS ----
// User on slot 8: "it was not dark matter. It was like desert and orange" â€” so
// either the ship-table slot numbers do not map straight onto what renders, or
// a name does not look like its name. Both are settled by LOOKING, and a build
// per guess is four minutes. In a dev build: hold CROUCH while holding a
// PACKED gun and it cycles the camo slot 1..75, one every 2.5 s, printing
// "CAMO SLOT n" (take -> give -> raise each step, the same lane the machine
// uses). Stand up to stop on one; the slot stays until the next crouch. The
// override above makes every give read the browsed slot, so the machine's
// own lanes cannot fight it. Never runs in last stand.
//
// v17.59 (2026-09-04) — THE BROWSER WAS READING HALF THE MENU, AND THE HALF IT
// SKIPPED IS THE ONE WITH THE ZOMBIES PACK-A-PUNCH CAMOS IN IT.
// A camo table is not one list of 75. Every weapon pack here carries FIVE
// weaponcamo assets under one weaponcamotable, at baseIndex 1 / 76 / 121 /
// 128 / 136, so the index space runs past 130 — and 76..89 and 121..125 are
// Der Eisendrache's six PaP camos, Zetsubou's island, Gorod Krovi's five and
// Revelations' five. The `slot > 75` wrap below meant this map had never once
// asked for a single one of them; every camo ever seen here came off the
// multiplayer half of the table.
//
// VERIFIED BEFORE WIDENING (all 167 GDTs in source_data that define a
// weaponcamo, plus the Leviathan's under _custom/wetegg): index -> material is
// IDENTICAL on every one of them from 1 to 126. Above 126 it stops being true —
// the Stormbreaker's third sub-table runs 121..136+ and its own list, so 128
// is loot_nightmare on the axe and blank on the guns. 73/74/75 and 127 are
// blank on every weapon, and 90..118 is the CWL esports block (twenty-nine
// slots, many of them the same shared material). All three are skipped here.
// ⚠️ TABLE SHAPE IS NOT PROOF OF RENDERING. Nothing above 75 has ever been on
// a gun in this map, and a material that does not resolve at runtime leaves the
// weapon in its base materials — i.e. a packed gun that looks unpacked, the
// exact failure this map spent four builds chasing. That is what the browse is
// FOR: the shortlist leads with the unseen band so one crouch answers it.
// (A first pass at this audit called the Executioner blank above 75. It is not —
// eight skye_t6_* packs indent some asset headers with FOUR SPACES instead of a
// tab, and a `^\t"name"` parser folds their DLC blocks into the previous asset
// and reports empties. Match GDT headers with `^[ \t]+`.)
function dev_camo_browser()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	self notify( "tod_camo_browser" );
	self endon( "tod_camo_browser" );

	list = dev_camo_browse_list();
	i = -1;
	for ( ;; )
	{
		wait 0.1;
		if ( !IsAlive( self ) || self laststand::player_is_in_laststand() )
			continue;
		if ( self GetStance() != "crouch" )
			continue;
		w = self GetCurrentWeapon();
		if ( !isdefined( w ) || w == level.weaponNone || pap_tier( self, w ) <= 0 )
			continue;
		i++;
		if ( i >= list.size )
			i = 0;
		self.tod_camo_browse = list[ i ];
		self camo_regive( w, true );
		IPrintLnBold( "CAMO SLOT " + list[ i ] + "   (" + ( i + 1 ) + " / " + list.size + ")" );
		wait 2.5;
	}
}

// The order the browser walks. Default is the SHORTLIST — the never-seen
// Pack-a-Punch band first, then the glow-mask camos in the proven band, then
// the two the map ships now as a reference point. ~35 slots, about 90 seconds
// of crouching, and the interesting half comes first.
// Flip full_sweep for the exhaustive 1..126 crawl (~97 slots, four minutes).
function dev_camo_browse_list()
{
	full_sweep = false;

	list = [];
	if ( full_sweep )
	{
		for ( s = 1; s <= 126; s++ )
		{
			if ( s >= 73 && s <= 75 )    continue;   // blank on every weapon
			if ( s == 83 )               continue;   // the one knife/gun rotation mismatch
			if ( s >= 90 && s <= 118 )   continue;   // the CWL esports block
			list[ list.size ] = s;
		}
		return list;
	}

	// unseen: the zombies Pack-a-Punch families, in map order
	list[ list.size ] = 76;    // Der Eisendrache PaP 01 .. 06
	list[ list.size ] = 77;
	list[ list.size ] = 78;
	list[ list.size ] = 79;
	list[ list.size ] = 80;
	list[ list.size ] = 81;
	list[ list.size ] = 82;    // Zetsubou No Shima PaP
	list[ list.size ] = 85;    // Gorod Krovi PaP base .. 04
	list[ list.size ] = 86;
	list[ list.size ] = 87;
	list[ list.size ] = 88;
	list[ list.size ] = 89;
	list[ list.size ] = 121;   // Revelations PaP 01 .. 05
	list[ list.size ] = 122;
	list[ list.size ] = 123;
	list[ list.size ] = 124;
	list[ list.size ] = 125;
	list[ list.size ] = 126;   // "lucid emissive"
	// proven band, carries a glow mask, never picked
	list[ list.size ] = 7;     // Shadows of Evil PaP — blue fractal over dark gold
	list[ list.size ] = 10;    // Nuketown — lit pipework
	list[ list.size ] = 27;    // ce_bo3 — 115's sibling, orange dashes
	list[ list.size ] = 34;    // ice
	list[ list.size ] = 49;    // jungle emissive
	list[ list.size ] = 52;    // scorch emissive
	list[ list.size ] = 55;    // flecktarn emissive
	list[ list.size ] = 60;    // dante emissive
	list[ list.size ] = 63;    // ardent emissive
	list[ list.size ] = 69;    // chameleon emissive
	list[ list.size ] = 71;    // heatstroke emissive
	list[ list.size ] = 84;    // section 9
	list[ list.size ] = 120;   // contract crystals
	// the reference points, last
	list[ list.size ] = 22;    // gold — PACK I today
	list[ list.size ] = 28;    // Element 115 — the old PACK III
	return list;
}
// ---- end dev camo browser ---------------------------------------------------

// PUBLIC â€” the second argument to GiveWeapon. Weapon options are a per-GIVE
// value: nothing re-reads them afterwards, so every give site that hands over a
// packed gun has to carry this or the camo silently reverts to the base look.
// That is exactly how the map lost the stock camo it was already being handed â€”
// swap_primary and the loadout gives call GiveWeapon with one argument.
function pap_camo_options( player, weapon )
{
	return player CalcWeaponOptions( pap_camo_index( player, weapon ), 0, 0, 0 );
}

// PUBLIC â€” give `weapon` wearing the right camo, and remember what we stamped.
function give_camo_weapon( weapon )
{
	if ( !isdefined( weapon ) || weapon == level.weaponNone )
	{
		roster_log( "GIVE_FAIL ent=" + self GetEntityNumber() + " reason=weapon_none" );
		return;
	}
	self GiveWeapon( weapon, pap_camo_options( self, weapon ) );
	roster_log( "GIVE ent=" + self GetEntityNumber() + " weapon=" + weapon.name + " owned=" + self HasWeapon( weapon ) );
	camo_stamp( weapon );
}

function roster_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_ROSTER] ms=" + GetTime() + " " + msg;
	/# PrintLn( line ); #/
}

// Dev-only loadout log (the RK5 reap). Assembled outside the developer block, printed
// inside it (the proven pattern, CLAUDE.md).
function loadout_dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) )
		return;
	line = "[TOD_LOADOUT] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

// PUBLIC â€” record what a give just stamped, so the watcher below knows this
// weapon is current and leaves it alone.
function camo_stamp( weapon )
{
	if ( !isdefined( weapon ) || weapon == level.weaponNone || !isdefined( weapon.name ) )
		return;
	if ( !isdefined( self.tod_camo_stamp ) )
		self.tod_camo_stamp = [];
	idx = pap_camo_index( self, weapon );
	self.tod_camo_stamp[ weapon.name ] = idx;
	if ( TOD_BREACHER_LOG && ( IsSubStr( weapon.name, "cc_mozambique" ) || IsSubStr( weapon.name, "cc_rem870" ) || IsSubStr( weapon.name, "cc_peacekeeper" ) ) )
	{
		line = "[TOD_BREACHER] GIVE ms=" + GetTime() + " ent=" + self GetEntityNumber() + " weapon=" + weapon.name
			+ " clip=" + self GetWeaponAmmoClip( weapon ) + " stock=" + self GetWeaponAmmoStock( weapon ) + " camo=" + idx;
		/# PrintLn( line ); #/
	}

	// ---- DEV DIAGNOSTIC (v17.36) â€” REMOVE WITH THE REST OF THE DEV HARNESS ----
	// The one question no amount of asset-ledger reading can answer: did this
	// lane RUN, and what did CalcWeaponOptions actually return? A nonzero index
	// with a zero options int means the options call is the fault, not the art.
	// IPrintLnBold is a free lane (no triggerstring slot) â€” see CLAUDE.md.
	// v17.43 â€” the options int is a uint64 and CANNOT be concatenated into a
	// string ("pair 'CAMO stamp ...' and 'uint64' has unmatching types"); the
	// throw killed the caller's thread â€” the per-player 1 s upkeep loop in
	// _tod_upgrades (twin reconcile, class-gun watchdog, second wind) â€” on
	// the first Pack-a-Punch of every dev session since v17.36 (console_mp.log
	// of the 18:02 match: every camo lane died at this line, the class gun's
	// swap never completed, and the player kept the BASE form in hand â€” so no
	// camo test before v17.45 ever looked at a packed gun).
	// v17.45 â€” THE uint64 IS NOT TOUCHED AT ALL. v17.43 replaced the concat
	// with `opts != 0`, but a uint64 compared against an int is the same
	// "unmatching types" pair as far as anyone has proven, and the failure
	// mode is the identical silent thread death. The only value that may ever
	// see that number is GiveWeapon's second argument. The print now answers
	// the one question that matters â€” did this lane run, with which index.
	if ( IS_TRUE( level.tod_dev ) && idx > 0 )
		IPrintLnBold( "CAMO stamp " + weapon.name + "  idx " + idx );
	// ---- end dev diagnostic --------------------------------------------------
}

// PUBLIC â€” RE-DRESS A WEAPON THE PLAYER ALREADY HOLDS (v17.39, 2026-09-04).
//
// Weapon options are a per-give value, and the one give that can change them
// on an owned asset is TAKE-THEN-GIVE. v17.35-37 called GiveWeapon on a weapon
// the player already had and hoped the options updated; stock never does that
// (zm_weapons::weapon_give branches on HasWeapon and only refills ammo), so it
// was an unproven engine behaviour â€” and it was the ONLY thing standing between
// the Pack-a-Punch buy and a camo, because the machine's own give goes through
// stock with stock's dead index. This is the proven shape instead: the same
// take -> give the 5,000 buy has done at the machine for months.
//
// `raise` = the weapon should end up in hand. Taking the CURRENT weapon makes the
// engine auto-raise something else in the same frame (ensure_equipped's lesson
// in _tod_upgrades), so a raised re-give is followed by a bounded, frame-paced
// re-assert until the engine agrees. Never fights last stand.
//
// Ammo is preserved by hand: GiveWeapon refills, and a re-dress is not a refill.
function camo_regive( weapon, raise )
{
	if ( !isdefined( weapon ) || weapon == level.weaponNone || !( self HasWeapon( weapon ) ) )
		return;
	clip  = self GetWeaponAmmoClip( weapon );
	stock = self GetWeaponAmmoStock( weapon );
	self TakeWeapon( weapon );
	self GiveWeapon( weapon, pap_camo_options( self, weapon ) );
	self SetWeaponAmmoClip( weapon, clip );
	self SetWeaponAmmoStock( weapon, stock );
	camo_stamp( weapon );
	if ( IS_TRUE( raise ) )
	{
		self SwitchToWeapon( weapon );
		self thread camo_regive_reassert( weapon );
	}
}

function private camo_regive_reassert( want )
{
	self endon( "disconnect" );
	level endon( "end_game" );
	self notify( "tod_camo_reassert" );   // newest re-give wins
	self endon( "tod_camo_reassert" );

	for ( i = 0; i < 30; i++ )   // up to 1.5s, the same bound as ensure_equipped
	{
		wait 0.05;
		if ( !isdefined( want ) || !( self HasWeapon( want ) ) )
			return;
		if ( self laststand::player_is_in_laststand() )
			return;
		if ( self GetCurrentWeapon() == want )
			return;
		self SwitchToWeaponImmediate( want );
	}
}

// THE BACKSTOP. Since v17.39 the machine path stamps the camo ITSELF
// (zm_cwpap::giveWeaponUpgraded after the 5,000 buy), so in a correct match this
// watcher never fires. It stays for the
// case nobody has thought of: a weapon whose stamp disagrees with its tier is
// re-dressed the next time it is HOLSTERED â€” a take/give of the current weapon
// is exactly the state the swap_primary block comment warns about (an eaten
// switch strands the player on the pistol), and a backstop must never be the
// thing that causes the map's worst-known bug.
//
// It NEVER touches a gun mid-swap (tod_swap_busy is _tod_upgrades' flag for
// exactly this) and never re-gives an unpacked gun.
function camo_watch()
{
	self endon( "disconnect" );
	self notify( "tod_camo_watch" );   // one per player across every respawn â€”
	self endon( "tod_camo_watch" );    // the map's idiom (_tod_perk_phd:414)

	for ( ;; )
	{
		wait 0.5;
		if ( !IsAlive( self ) || IS_TRUE( self.tod_swap_busy ) )
			continue;
		if ( self laststand::player_is_in_laststand() )
			continue;

		primaries = self GetWeaponsListPrimaries();
		foreach ( w in primaries )
			self restamp_camo( w );
	}
}

function private restamp_camo( w )
{
	if ( !isdefined( w ) || w == level.weaponNone || !isdefined( w.name ) )
		return;

	want = pap_camo_index( self, w );
	if ( want <= 0 )
		return;   // unpacked: nothing to wear, and a re-give would cost ammo for no reason

	if ( !isdefined( self.tod_camo_stamp ) )
		self.tod_camo_stamp = [];
	if ( isdefined( self.tod_camo_stamp[ w.name ] ) && self.tod_camo_stamp[ w.name ] == want )
		return;

	// HOLSTERED ONLY â€” see the block comment above. The gun in hand is left for
	// the next tick; the stamp stays stale until then, so nothing is forgotten.
	cur = self GetCurrentWeapon();
	if ( cur == w || cur == level.weaponNone )
		return;

	self camo_regive( w, false );   // take -> give, ammo preserved, stamp written
}

// ---------------------------------------------------------------------------
// PACK-A-PUNCH SELF-REPAIR (2026-08-23)
// ---------------------------------------------------------------------------
// Stock PaP resolves an upgrade PURELY through level.zombie_weapons[base].upgrade,
// which is built once from the weapons stringtable. If a row's upgrade_name does
// not resolve to a real weapon, stock stores weaponNone there â€” and because
// weaponNone IS a defined value, can_upgrade_weapon() answers TRUE. The machine
// then takes the points and hands back nothing. That failure is completely
// silent: no error, no log, PaP just "doesn't work".
//
// This pass runs after the table is built and re-points any class-gun row whose
// upgrade is missing at the weapon we KNOW is linked, found through
// weapon_or_zm() so it works whichever spelling the engine ended up using. It
// repairs the symptom regardless of which of the three name sources is at
// fault, which is what a beta needs â€” the alternative is another guess.
//
// It only ever touches rows for OUR registered class guns, and only rows that
// are already broken, so a correct table is left completely untouched.
function repair_weapon_table()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );

	made = 0;
	foreach ( ck in GetArrayKeys( level.tod_classes ) )
	{
		c = level.tod_classes[ ck ];
		for ( t = 1; t <= c.tiers.size; t++ )
		{
			g = c.tiers[ t ];
			if ( !isdefined( g ) )
				continue;
			made += repair_gun_rows( g );
		}
	}
	level.tod_pap_rows_repaired = made;
}

// Walk every ladder combination this gun can reach and make sure the weapons
// table carries a row whose upgrade RESOLVES. Level bound is a flat 0..5: the
// real caps live in the generator's AXIS table and in add_domain, and importing
// _tod_upgrades to read them would be a cycle (it imports us). Over-scanning is
// free â€” a combination that does not exist simply fails to resolve and is
// skipped, and this runs once at level start.
function repair_gun_rows( g )
{
	n = 0;
	if ( !isdefined( g.axes ) || g.axes.size == 0 )
		return repair_one_row( g, "_b" );

	if ( g.axes.size == 1 )
	{
		for ( a = 0; a <= 5; a++ )
			n += repair_one_row( g, "_" + g.axes[ 0 ].letter + a );
		return n;
	}

	for ( a = 0; a <= 5; a++ )
	{
		for ( b = 0; b <= 5; b++ )
			n += repair_one_row( g, "_" + g.axes[ 0 ].letter + a + g.axes[ 1 ].letter + b );
	}
	return n;
}

// One (base, PaP) pair. Returns 1 if it (re-)registered the pair.
//
// WHY RE-REGISTER RATHER THAN PATCH THE STRUCT: stock's own add_zombie_weapon
// builds the row exactly the way PaP expects (including weapon_classname and
// the zombie_weapons_upgraded back-reference). Hand-building a struct that only
// LOOKS right is how a silent half-fix happens.
//
// AND WHY IT DOES NOT MATTER which spelling is correct: resolved_name() returns
// whichever of "<name>" / "<name>_zm" actually resolves to a linked weapon, so
// this repairs the table under either engine behaviour. That is deliberate â€”
// the naming question cost two wrong fixes on 2026-08-23 and this closes it by
// asking the engine at runtime instead of inferring from build artifacts.
function repair_one_row( g, suffix )
{
	base_n = resolved_name( variant_name( g, false, suffix ) );
	if ( !isdefined( base_n ) )
		return 0;
	up_n = resolved_name( variant_name( g, true, suffix ) );
	if ( !isdefined( up_n ) )
		return 0;

	base_w = GetWeapon( base_n );
	if ( isdefined( level.zombie_weapons ) && isdefined( level.zombie_weapons[ base_w ] ) )
	{
		st = level.zombie_weapons[ base_w ];
		if ( isdefined( st.upgrade ) && st.upgrade != level.weaponNone )
			return 0;   // already correct â€” leave stock's row exactly as it is
	}

	// include first: add_zombie_weapon early-returns on a non-included weapon.
	zm_utility::include_weapon( base_n, false );
	zm_utility::include_weapon( up_n, false );
	zm_weapons::add_zombie_weapon( base_n, up_n, undefined, 1250, "rifle", undefined, undefined, undefined, false, "" );
	return 1;
}

// -> the spelling of `name` that resolves to a real weapon, or undefined.
function resolved_name( name )
{
	if ( !isdefined( name ) || name == "" )
		return undefined;
	w = GetWeapon( name );
	if ( isdefined( w ) && w != level.weaponNone )
		return name;
	w = GetWeapon( name + "_zm" );
	if ( isdefined( w ) && w != level.weaponNone )
		return name + "_zm";
	return undefined;
}

// PUBLIC â€” GetWeapon for a variant name, tolerant of the "_zm" asset tail.
// Every shipped precedent says the bare name is the right one (see the block in
// register_guns), so that is tried FIRST; the tailed form is a belt-and-braces
// fallback so a future port that behaves differently degrades to "works"
// instead of "the upgrade silently does nothing", which is how the blade bug
// hid for weeks.
function weapon_or_zm( name )
{
	if ( !isdefined( name ) || name == "" )
		return undefined;
	w = GetWeapon( name );
	if ( isdefined( w ) && w != level.weaponNone )
		return w;
	w = GetWeapon( name + "_zm" );
	if ( isdefined( w ) && w != level.weaponNone )
		return w;
	return undefined;
}

function axes1( d1, l1 )
{
	a = [];
	a[ 0 ] = axis( d1, l1 );
	return a;
}

function axes2( d1, l1, d2, l2 )
{
	a = [];
	a[ 0 ] = axis( d1, l1 );
	a[ 1 ] = axis( d2, l2 );
	return a;
}

function axis( domain, letter )
{
	x = SpawnStruct();
	x.domain = domain;
	x.letter = letter;
	return x;
}

// STEM-PREFIX TRAP: is_class_primary matches by substring, so two stems in one
// ladder where one is a prefix of the other ("t9_mp5" / "t9_mp5k") would
// cross-match. Identical stems (the null ladder) are fine. Dev-visible only.
function check_stem_prefixes()
{
	foreach ( c in level.tod_classes )
	{
		for ( i = 1; i <= TOD_TIER_MAX; i++ )
		{
			for ( j = 1; j <= TOD_TIER_MAX; j++ )
			{
				if ( i == j || !isdefined( c.tiers[ i ] ) || !isdefined( c.tiers[ j ] ) )
					continue;
				a = c.tiers[ i ].stem;
				b = c.tiers[ j ].stem;
				if ( a != b && IsSubStr( b, a ) )
				{
					level.tod_stem_clash = a + " < " + b;
					/# PrintLn( "^1[tod] STEM PREFIX CLASH in class " + c.key + ": " + a + " is a prefix of " + b ); #/
				}
			}
		}
	}
}

// ---------------------------------------------------------------------------
// Lookups â€” every "what gun does this player hold" question goes through here
// ---------------------------------------------------------------------------

function tier_max()
{
	return TOD_TIER_MAX;
}

function get_class( player )
{
	if ( !isdefined( player ) || !isdefined( player.tod_class ) )
		return undefined;
	return level.tod_classes[ player.tod_class ];
}

// The player's tier (1 until a TIER card is taken).
function tier( player )
{
	if ( !isdefined( player ) || !isdefined( player.tod_tier ) )
		return 1;
	return player.tod_tier;
}

// 1..4 for the draft / tier-card class code, 0 if unknown.
function class_id( key )
{
	if ( !isdefined( key ) || !isdefined( level.tod_classes[ key ] ) )
		return 0;
	return level.tod_classes[ key ].id;
}

function gun_at( class_key, t )
{
	if ( !isdefined( class_key ) || !isdefined( level.tod_classes[ class_key ] ) )
		return undefined;
	c = level.tod_classes[ class_key ];
	// a tier with no registered gun falls back to the highest registered
	// below it â€” never hand out nothing
	for ( i = t; i >= 1; i-- )
	{
		if ( isdefined( c.tiers[ i ] ) )
			return c.tiers[ i ];
	}
	return undefined;
}

// The gun struct the player holds NOW (their class + tier), or undefined.
function gun( player )
{
	if ( !isdefined( player ) || !isdefined( player.tod_class ) )
		return undefined;
	return gun_at( player.tod_class, tier( player ) );
}

// The gun the NEXT tier would hand out, or undefined at the top.
function next_gun( player )
{
	if ( !isdefined( player ) || !isdefined( player.tod_class ) )
		return undefined;
	t = tier( player ) + 1;
	if ( t > TOD_TIER_MAX )
		return undefined;
	if ( !isdefined( level.tod_classes[ player.tod_class ].tiers[ t ] ) )
		return undefined;
	return level.tod_classes[ player.tod_class ].tiers[ t ];
}

function gun_stem( player )
{
	g = gun( player );
	if ( !isdefined( g ) )
		return undefined;
	return g.stem;
}

// The level-0 variant suffix of a gun ("_f0h0" / "_r0m0" / "_p0" / "_k0", or
// "_b" for an axis-less gun) â€” the form give_class_loadout and a tier-up hand
// out; _tod_upgrades::reconcile_twin then walks it to the player's levels.
function base_suffix( g )
{
	if ( !isdefined( g ) || !isdefined( g.axes ) || g.axes.size == 0 )
		return "_b";
	s = "_";
	for ( i = 0; i < g.axes.size; i++ )
		s += g.axes[ i ].letter + "0";
	return s;
}

// The weapon object for a gun's level-0 form; falls back to the RAW stem (the
// four T1 raw assets are zoned) and finally undefined â€” callers must check.
function base_weapon( g )
{
	if ( !isdefined( g ) )
		return undefined;
	w = weapon_or_zm( variant_name( g, false, base_suffix( g ) ) );
	if ( isdefined( w ) && w != level.weaponNone )
		return w;
	w = GetWeapon( g.stem );
	if ( isdefined( w ) && w != level.weaponNone )
		return w;
	return undefined;
}

// ---------------------------------------------------------------------------
// Spawn / give
// ---------------------------------------------------------------------------

// self = player. Fires on every spawn (initial + round respawns) â€” re-give
// the loadout every time (respawned players lose weapons). Class assignment:
// the game-start draft (_tod_class_select) owns it; a classless player only
// gets a RANDOM class here when they arrive AFTER the draft closed (drop-in
// join). Before/during the draft, stay classless â€” the draft assigns.
function on_player_spawned()
{
	self endon( "disconnect" );

	if ( !isdefined( self.tod_class ) && IS_TRUE( level.tod_class_select_done ) )
		assign_class( self, random_class_key() );

	self thread give_class_loadout();   // no-op while still classless
	self thread apply_class_body_on_spawn();
	self thread camo_watch();           // self-cancelling: one watcher per player
	if ( IS_TRUE( level.tod_dev ) )
		self thread dev_camo_browser();   // v17.54 dev: crouch with a packed gun to cycle camo slots
	if ( IS_TRUE( level.tod_dev_all_guns ) )
		self thread dev_all_guns_watch();   // 2026-09-25 dev: every gun of the class
}

// DEV: EVERY GUN OF YOUR CLASS (2026-09-25, user: "in dev mode, I need all of
// the weapons for that class ... I'm testing out every single one of them").
// level.tod_dev_all_guns (zm_tod2_cybercity.gsc; the publish gate catches it).
// Keeps all three tiers' primaries AND all three tiers' sidearms in hand -- six
// per class -- and removes any gun that belongs to ANOTHER class, so a class
// switch at a station swaps the whole set. Polled, so a respawn, a promotion
// (whose give_secondary reaps the other sidearms) or a class switch refills
// within TOD_DEV_ALL_GUNS_POLL. Only the CURRENT tier's gun is "the class gun"
// for cards; the others test at their base numbers. One watcher per player.
function dev_all_guns_watch()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	if ( IS_TRUE( self.tod_dev_all_guns_on ) ) return;
	self.tod_dev_all_guns_on = true;
	last_key = "";
	for ( ;; )
	{
		wait TOD_DEV_ALL_GUNS_POLL;
		if ( !isdefined( self.tod_class ) || !isalive( self ) || self laststand::player_is_in_laststand() )
			continue;
		key = self.tod_class;
		c = level.tod_classes[ key ];
		if ( !isdefined( c ) || IS_TRUE( c.additive ) )
			continue;
		// another class's primaries or sidearms out
		keys = GetArrayKeys( level.tod_classes );
		foreach ( ok in keys )
		{
			if ( ok == key ) continue;
			oc = level.tod_classes[ ok ];
			for ( t = 1; t <= 3; t++ )
			{
				stems = [];
				if ( isdefined( oc.tiers[ t ] ) ) stems[ stems.size ] = oc.tiers[ t ].stem;
				ss = secondary_stem( ok, t );
				if ( isdefined( ss ) && ss != "" ) stems[ stems.size ] = ss;
				held = self GetWeaponsListPrimaries();
				foreach ( st in stems )
				{
					foreach ( w in held )
					{
						if ( isdefined( w ) && isdefined( w.name ) && IsSubStr( w.name, st ) && !holds_own_stem( key, w.name ) && self HasWeapon( w ) )
							self TakeWeapon( w );
					}
				}
			}
		}
		gave = 0;
		for ( t = 1; t <= 3; t++ )
		{
			g = c.tiers[ t ];
			if ( isdefined( g ) && !( self has_gun( g ) ) )
			{
				w = base_weapon( g );
				if ( isdefined( w ) && w != level.weaponNone )
				{
					self give_camo_weapon( w );
					self GiveStartAmmo( w );
					gave++;
				}
			}
			ss = secondary_stem( key, t );
			if ( isdefined( ss ) && ss != "" && !( self holds_secondary_stem( ss ) ) )
			{
				sw = GetWeapon( secondary_name( key, t ) );
				if ( isdefined( sw ) && sw != level.weaponNone )
				{
					self give_camo_weapon( sw );
					self GiveStartAmmo( sw );
					gave++;
				}
			}
		}
		now_held = self GetWeaponsListPrimaries();
		held_n = now_held.size;
		if ( gave > 0 || key != last_key )
			roster_log( "DEV_ALL_GUNS class=" + key + " gave=" + gave + " held=" + held_n );
		last_key = key;
	}
}

// true if `name` matches one of `key`'s own primary or sidearm stems (a stem
// shared between classes, e.g. a sidearm, is never reaped from its owner).
function private holds_own_stem( key, name )
{
	c = level.tod_classes[ key ];
	for ( t = 1; t <= 3; t++ )
	{
		if ( isdefined( c.tiers[ t ] ) && IsSubStr( name, c.tiers[ t ].stem ) ) return true;
		ss = secondary_stem( key, t );
		if ( isdefined( ss ) && ss != "" && IsSubStr( name, ss ) ) return true;
	}
	return false;
}

// =============================================================================
// PER-CLASS PLAYER MODEL (v16.18, user 2026-09-02)
//
// The four SHADOWS OF EVIL bodies, picked for silhouette spread â€” on a spiral
// you read a teammate as a SHAPE twenty floors up, never as a texture:
//
//     5  Floyd Campbell   (boxer)      -> HEAVY       the only real mass
//     6  Jack Vincent     (detective)  -> ASSAULT     the neutral baseline
//     7  Jessica Rose     (femme)      -> SKIRMISHER  lightest outline
//     8  Nero Blackstone  (magician)   -> SLASHER     caped, theatrical
//
// WHERE THE INDEX COMES FROM, because a wrong body is a silent cosmetic bug
// nobody reports: the index is the position in core_common.csv's own body list,
// and all FOUR known values fit that ordering with nothing left over --
//     0 dempsey  1 nikolai  2 richtofen  3 takeo
//     4 beast    5 boxer    6 detective  7 femme     8 magician
// boxer 5 / detective 6 / femme 7 / magician 8 are the four already shipping,
// so the mapping is DERIVED from four confirmations, not guessed from one.
// Body 0 (Dempsey) is the classless body (apply_class_body_on_spawn).
//
// NO DOWNLOAD, NO GDT, NO ZONE LINE. All four bodies AND their viewhands /
// viewlegs / viewbody are already in `zone_source/all/assetlist/core_common.csv`
// (verified 2026-09-02: `grep -cE "^xmodel,c_zom_(der|zod)_[a-z]+_mpc_fb$"`
// returns 9). core_common ships with the base game, so they resolve on every
// player's machine â€” this cannot hit the usermap white-square trap, which is
// about referencing assets that are NOT in an assetlist.
//
// ---------------------------------------------------------------------------
// TRAP 1 â€” WHY `characterIndex` IS DELIBERATELY NOT TOUCHED.
// The obvious implementation is `self.characterIndex = 7` and letting stock's
// zm_usermap::giveCustomCharacters() apply it. That is WRONG and would ship a
// silent audio bug: stock's set_exert_id() does
//     self zm_audio::SetExertVoice( self.characterIndex + 1 )
// and SetExertVoice writes the "charindex" clientfield, registered in
// _zm_audio.gsc:29 as **3 BITS** â€” max value 7. Body 7 would send 8 and body 8
// would send 9; both overflow, wrapping the exert voice to 0 and 1. Anything
// else keyed on characterIndex (laststand's per-round revive counters, the vox
// system's "vox_plr_<idx>_" aliases) is likewise built for 0..3.
// So: characterIndex STAYS whatever stock assigned. Only the BODY moves.
// Voice and body do not have to match, and this map's exert set only covers
// 1..4 anyway (see the level.exert_sounds note in _tod_perk_drink.gsc).
//
// TRAP 2 â€” STOCK RE-APPLIES THE BODY ON EVERY RESPAWN.
// giveCustomCharacters() runs on each spawn and unconditionally calls
// SetCharacterBodyType( self.characterIndex ) â€” so a one-shot set at draft time
// is reverted the first time the player goes down. Hence the re-assert below,
// behind the same `wait 0.5` that give_class_loadout() already uses to let the
// stock spawn path finish. (Its OTHER stomp, SetMoveSpeedScale(1), was already
// solved: body_systems_loop() in _tod_upgrades.gsc re-asserts move speed every
// second for exactly this reason.)
//
// SetCharacterBodyType RESETS body style and helmet style to defaults, so both
// must be re-applied after it â€” a missing helmet style is how you get a
// headless or wrongly-helmeted character. Stock does the same three calls in
// the same order.
// =============================================================================
function class_body_index( key )
{
	switch ( key )
	{
		case "heavy":      return 5;   // Floyd Campbell  (c_zom_zod_boxer_mpc_fb)
		case "assault":    return 6;   // Jack Vincent    (c_zom_zod_detective_mpc_fb)
		case "necromancer": return 7;   // Jessica Rose    (c_zom_zod_femme_mpc_fb)
		case "slasher":    return 8;   // Nero Blackstone (c_zom_zod_magician_mpc_fb)
	}
	return undefined;
}

// self = player. Safe to call any time; no-op while still classless.
function apply_class_body()
{
	if ( !isdefined( self.tod_class ) || !IsAlive( self ) )
		return;

	idx = class_body_index( self.tod_class );
	if ( !isdefined( idx ) )
		return;

	self SetCharacterBodyType( idx );
	self SetCharacterBodyStyle( 0 );     // bodytype reset wiped these two
	self SetCharacterHelmetStyle( 0 );
}

function apply_class_body_on_spawn()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	wait 0.5;   // let stock giveCustomCharacters() set its body first
	if ( !isdefined( self.tod_class ) )
	{
		// BEFORE THE DRAFT NOBODY WEARS A CLASS BODY (2026-09-09, user: "when
		// selecting a class there should be no class icon on the player HUD").
		// Stock hands joiners the four Primis bodies in order, and a body's
		// portrait id can map to a class medallion, so a classless player could
		// wear one for the whole draft. Everyone classless now wears body 0
		// (Dempsey, char3), whose portrait id maps to no medallion.
		// apply_class_body() replaces it the moment a class lands.
		if ( IsAlive( self ) )
		{
			self SetCharacterBodyType( 0 );
			self SetCharacterBodyStyle( 0 );
			self SetCharacterHelmetStyle( 0 );
		}
		return;
	}
	self apply_class_body();
}

// The random class a DROP-IN JOINER gets (on_player_spawned) and the
// class_select sweep's fallback both come through here.
//
// DRAFTABLE-ONLY SINCE 2026-09-07. This reads the class REGISTRY, not the
// draft's id table, so it is the ONE lane that can hand out a class the draft
// never offers. A class registered for build-out (not draftable) must be
// unreachable by it: the joiner would get a class with no cards on screen and,
// before the assets land, no weapon at all.
function random_class_key()
{
	keys = [];
	all = GetArrayKeys( level.tod_classes );
	foreach ( k in all )
	{
		if ( IS_TRUE( level.tod_classes[ k ].draftable ) )
			keys[ keys.size ] = k;
	}
	if ( keys.size == 0 )
		return "assault";   // the same last-resort key class_key() falls back to
	return keys[ RandomInt( keys.size ) ];
}

function assign_class( player, key )
{
	player.tod_class = key;
	if ( !isdefined( player.tod_tier ) )
		player.tod_tier = 1;
	player notify( "tod_class_assigned" );

	// The draft lands on an ALREADY-SPAWNED player, so the spawn-side
	// re-assert has long since run â€” apply the body here too, or the first
	// life of the match wears whatever stock rolled.
	player apply_class_body();
}

// self = player. Gives the CURRENT TIER's gun (a respawn after a tier-up gets
// the promoted gun, never the T1 one), its alt, and the secondary.
function give_class_loadout()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	g = gun( self );
	if ( !isdefined( g ) )
		return;

	wait 0.5;   // let the stock loadout give (start pistol) finish first

	if ( !( self has_gun( g ) ) )
	{
		want = base_weapon( g );
		if ( isdefined( want ) )
		{
			self give_camo_weapon( want );   // stamps the camo for the form's tier (0 on a base gun)
			self GiveStartAmmo( want );
			self SwitchToWeapon( want );
		}
	}

	// ADDITIVE CLASS (v18.30): inert today - no registered class sets
	// .additive. Such a class keeps every LOWER tier's gun too, so a respawn
	// at tier 3 comes back with all three. Given in the holster -- the
	// current tier's gun above is the one raised.
	if ( IS_TRUE( level.tod_classes[ g.class_key ].additive ) )
	{
		for ( t = 1; t < tier( self ); t++ )
		{
			lg = level.tod_classes[ g.class_key ].tiers[ t ];
			if ( !isdefined( lg ) || self has_gun( lg ) )
				continue;
			lw = base_weapon( lg );
			if ( isdefined( lw ) )
			{
				self give_camo_weapon( lw );
				self GiveStartAmmo( lw );
			}
		}
	}

	// the alt melee (the slasher's bowie replaces the base knife everywhere)
	if ( isdefined( g.alt ) )
	{
		alt = GetWeapon( g.alt );
		if ( isdefined( alt ) && alt != level.weaponNone && !( self HasWeapon( alt ) ) )
			self GiveWeapon( alt );
	}

	// TIER-KEYED: a respawn after a tier-up must hand back the sidearm that
	// matches the promoted gun, exactly the way the primary already does
	// (`gun( self )` above resolves by tier). Passing the class alone would
	// quietly demote every player back to their T1 sidearm on death.
	self give_secondary( g.class_key, tier( self ) );
}

// self = player. Strip any OTHER class's sidearm before handing out this
// class's. Needed the moment secondaries went per-class: the base stations let
// a player switch class mid-run, and sidearms sit in PRIMARY slots â€” so without
// this, one switch leaves you holding two and the stock too-many-weapons
// monitor that would normally reap the extra is deliberately OFF on this map
// (v9.18: it was confiscating class guns). Matched on the STEM, because the
// PaP form is a separate asset name â€” "t9_amp63_rdw_up_zm" and "s1_bulldog_up"
// both have to be caught, not just the base.
function take_foreign_secondaries( keep_stem )
{
	// MATCH on the stems, never on the give names â€” see the TOD_SEC_* block.
	// ALL TWELVE, not just this class's three. A player who switches class at a
	// base station keeps whatever they were carrying, so the sidearm to reap can
	// belong to any class AND any tier â€” and since v10.24 a tier-up inside one
	// class also has an old sidearm to clear. Reaping only the current class's
	// rows would leave the tier-1 shotgun in a primary slot next to the tier-3
	// one, which is precisely the two-sidearms bug this function exists to stop.
	stems = secondary_all_stems();

	weapons = self GetWeaponsListPrimaries();
	for ( i = 0; i < weapons.size; i++ )
	{
		w = weapons[ i ];
		if ( !isdefined( w ) || !isdefined( w.name ) )
			continue;
		// THE RK5 (map 1's v19.55, ported 2026-10-04). No class owns it, so it is always
		// foreign. The override beside level.start_weapon (zm_tod2_cybercity.gsc) stops
		// stock's Easter-egg reward from handing it out; this is the repair lane if anything
		// ever does, on every loadout path (give_secondary runs this reap although no class
		// carries a sidearm). It should never fire, which is why it logs.
		if ( IsSubStr( w.name, TOD_RK5_STEM ) )
		{
			self TakeWeapon( w );
			loadout_dev_log( "RK5 reaped weapon=" + w.name + " player=" + self GetEntityNumber() );
			continue;
		}
		if ( isdefined( keep_stem ) && keep_stem != "" && IsSubStr( w.name, keep_stem ) )
			continue;   // the sidearm we are keeping, in any form â€” leave it
		for ( j = 0; j < stems.size; j++ )
		{
			if ( stems[ j ] == keep_stem )
				continue;
			if ( IsSubStr( w.name, stems[ j ] ) )
			{
				self TakeWeapon( w );
				break;
			}
		}
	}
}

// PUBLIC â€” every sidearm match stem in the map, all four classes x three tiers.
function secondary_all_stems()
{
	return array( TOD_SECSTEM_NECROMANCER_1, TOD_SECSTEM_NECROMANCER_2, TOD_SECSTEM_NECROMANCER_3,
	              TOD_SECSTEM_ASSAULT_1,    TOD_SECSTEM_ASSAULT_2,    TOD_SECSTEM_ASSAULT_3,
	              TOD_SECSTEM_HEAVY_1,      TOD_SECSTEM_HEAVY_2,      TOD_SECSTEM_HEAVY_3,
	              TOD_SECSTEM_SLASHER_1,    TOD_SECSTEM_SLASHER_2,    TOD_SECSTEM_SLASHER_3 );
}

// A tier clamped into 1..TOD_TIER_MAX. Every lookup below runs through this so
// an undefined or out-of-range tier can never fall off the end of a switch and
// return a sidearm for a tier that does not exist.
function sec_tier_clamp( tier )
{
	if ( !isdefined( tier ) || tier < 1 )
		return 1;
	if ( tier > TOD_TIER_MAX )
		return TOD_TIER_MAX;
	return tier;
}

// PUBLIC â€” the sidearm ASSET NAME for a (class, tier). An unknown class falls
// back to the starter pistol, which is always registered, so a classless or
// mis-keyed player can never end up with no secondary at all.
function secondary_name( class_key, tier )
{
	// NO SECONDARIES IN TOWER II (user 2026-09-26: "they have secondaries that
	// we never even defined ... carryover from Tower of Doom One ... make sure
	// those get removed for all the classes"). Every class is primary-only.
	// The lookups answer "" for every
	// (class, tier), give_secondary reaps whatever sidearm stock's spawn or a
	// Tower One save left in the hands and grants nothing, and the tier-up
	// path (_tod_upgrades) gets the same answer. The TOD_SEC_* / TOD_SECSTEM_*
	// rows above are KEPT for exactly one reader, secondary_all_stems(): the
	// reap has to recognise the twelve old sidearms in any form to take them.
	// The unused sidearm assets themselves leave in a later FULL build
	// (gen_tod_twins, lead-only).
	return "";
}

// PUBLIC - the MATCH STEM for a (class, tier). "" for every class since
// 2026-09-26 (see secondary_name); kept as a function because the dev
// all-guns lane, the reap and the tier-up path all ask it.
function secondary_stem( class_key, tier )
{
	return "";
}

// PUBLIC â€” self = player. Swap the sidearm to the one this (class, tier) owns.
// Called by the tier-up path and by give_class_loadout via its own inline pair.
// Returns true if the player is holding the right sidearm when it returns.
function give_secondary( class_key, tier )
{
	keep = secondary_name( class_key, tier );
	self take_foreign_secondaries( secondary_stem( class_key, tier ) );
	// Clean first: stock spawn and a previous class can leave a sidearm,
	// including pistol_standard_upgraded (Death and Taxes). Empty means NONE,
	// not the heavy's fallback pistol. Every grant path uses this helper.
	if ( !isdefined( keep ) || keep == "" )
		return false;

	w = GetWeapon( keep );
	if ( !isdefined( w ) || w == level.weaponNone )
		return false;

	// OWNERSHIP IS TESTED ON THE STEM, NOT THE BASE NAME (2026-08-25).
	//
	// HasWeapon( base ) is FALSE once the sidearm has been Pack-a-Punched â€” the
	// PaP form is a different asset (t8_sg12_up_b, not t8_sg12_b). So a player
	// who packs their secondary and then respawns, switches class, or tiers up
	// was handed a SECOND, un-packed copy of it: two sidearms in primary slots,
	// on a map where the stock too-many-weapons monitor is deliberately OFF
	// (v9.18). take_foreign_secondaries cannot save us either â€” it matches the
	// same stem and correctly leaves the packed one alone.
	//
	// This is the same rule has_gun() already applies to the class primary: hold
	// ANY form of it and you own it. It matters far more now that packing a
	// secondary before the primary is a normal thing to do.
	if ( self holds_secondary_stem( secondary_stem( class_key, tier ) ) )
		return true;

	self give_camo_weapon( w );
	self GiveStartAmmo( w );
	return true;
}

// self = player. Holds ANY form (base / PaP / twin variant) of a sidearm stem.
function holds_secondary_stem( stem )
{
	if ( !isdefined( stem ) || stem == "" )
		return false;
	weapons = self GetWeaponsListPrimaries();
	foreach ( w in weapons )
	{
		if ( isdefined( w ) && isdefined( w.name ) && IsSubStr( w.name, stem ) )
			return true;
	}
	return false;
}

// PUBLIC â€” self = player. Pack-a-Punch this player's CURRENT sidearm IN PLACE.
// Written for the retired Endless Spire's ascension grant (v15); its one
// caller now is tod_upgrades::dev_grant_maxed, which climbs the tiers and
// latches tod_pap_owned for the PRIMARY but never touches
// the sidearm â€” tod_pap_owned is consumed only by reconcile_twin, and that
// stem-matches the class primary (_tod_upgrades.gsc:2150-2151), so the sidearm
// is structurally unreachable from the grant.
//
// WHY THE STOCK PATH HERE AND THE LATCH THERE: the free-PaP drop's header
// records that can_upgrade_weapon/get_upgrade_weapon "PaP'd the PISTOL fine but
// never the class guns" â€” the twins are what the stock gates reject. A sidearm
// is NOT a twin (no variant axes, one plain `_up` row apiece in
// zm_levelcommon_weapons.csv, verified for all twelve), so it is exactly the
// case the stock path demonstrably handles.
//
// NO SwitchToWeapon, deliberately: the grant hands the player a maxed T3
// primary and this must not yank it out of their hands mid-grant.
// Returns true if the sidearm is packed when it returns.
function pap_secondary()
{
	c = get_class( self );
	if ( !isdefined( c ) )
		return false;   // classless (pre-draft) â€” nothing to pack
	stem = secondary_stem( c.key, tier( self ) );
	if ( !isdefined( stem ) || stem == "" )
		return false;

	// Find the live sidearm OBJECT by stem, so this works whichever form the
	// player is carrying (base, or a twin-suffixed one if that ever changes).
	cur = undefined;
	weapons = self GetWeaponsListPrimaries();
	foreach ( w in weapons )
	{
		if ( isdefined( w ) && isdefined( w.name ) && IsSubStr( w.name, stem ) )
		{
			cur = w;
			break;
		}
	}
	if ( !isdefined( cur ) )
		return false;   // not carrying it â€” give_secondary owns that repair

	// ALREADY PACKED? Test the NAME, not is_weapon_upgraded. Three of the
	// twelve sidearm rows name forms that is_weapon_upgraded cannot see (the
	// weapons-CSV `_zm` suffix mismatch), and its answer comes from
	// level.zombie_weapons_upgraded, which those rows never populate. The `_up`
	// substring is the one test that is true for every packed sidearm in this
	// map â€” including the two DUAL-WIELD forms (t9_amp63_rdw_up,
	// t6_executioner_rdw_up_b), which no other test catches either.
	if ( IsSubStr( cur.name, "_up" ) )
		return true;

	// Offhand guard, same reason as the free-PaP drop's: nothing here ever
	// wants to Pack-a-Punch a tactical, and can_upgrade_weapon has no such
	// exclusion of its own.
	if ( zm_utility::is_offhand_weapon( cur ) )
		return false;
	if ( !( zm_weapons::can_upgrade_weapon( cur ) ) )
		return false;

	up = zm_weapons::get_upgrade_weapon( cur, false );
	if ( !isdefined( up ) )
		return false;

	self TakeWeapon( cur );
	up = self zm_weapons::weapon_give( up );
	if ( !isdefined( up ) )
	{
		// give failed â€” hand the original back rather than strand them with a
		// primary slot short, on a map that runs the too-many-weapons monitor
		// deliberately OFF and so would never notice.
		self zm_weapons::weapon_give( cur );
		return false;
	}
	self GiveStartAmmo( up );
	self notify( "weapon_give", up );
	return true;
}

// PUBLIC â€” is this weapon the player's CLASS SECONDARY (the sidearm their
// current class+tier owns), in any form: base, PaP, or the dual-wield halves?
//
// The exact mirror of is_class_primary below, and written the same way for the
// same reason: the stem match covers every form, so a PaP'd or dual-wielded
// sidearm still answers true. That matters more here than for primaries â€”
// TWO of the twelve sidearms PaP into `_rdw` dual-wield pairs (t9_amp63 and
// t6_executioner), and a name-equality test would silently miss both.
//
// Added v16 for the slasher's anti-elite sidearm bonus; kept general because
// nothing about it is slasher-specific and the next caller should not have to
// re-derive it.
function is_class_secondary( player, weapon )
{
	if ( !isdefined( player ) || !isdefined( weapon ) || !isdefined( weapon.name ) )
		return false;
	c = get_class( player );
	if ( !isdefined( c ) )
		return false;                       // classless (pre-draft)
	stem = secondary_stem( c.key, tier( player ) );
	if ( !isdefined( stem ) || stem == "" )
		return false;
	return IsSubStr( weapon.name, stem );
}

// self = player. Holds ANY form (base / PaP / twin variant) of gun g.
function has_gun( g )
{
	if ( !isdefined( g ) )
		return false;
	weapons = self GetWeaponsListPrimaries();
	foreach ( w in weapons )
	{
		if ( isdefined( w ) && IsSubStr( w.name, g.stem ) )
			return true;
	}
	return false;
}

// ADDITIVE CLASSES (v18.30): inert today - no registered class sets .additive.
// For such a class every gun registered at or below the player's tier is a
// class primary -- a tier-1 gun it kept is as much "the class gun" as the one
// the promotion just handed out. For every other class this is exactly the
// current-tier gun, as before.
// Resolve retained primaries as well as the current tier for variant swaps.
function gun_for_weapon( player, weapon )
{
	if ( !isdefined( weapon ) || !isdefined( weapon.name ) )
		return undefined;
	g = gun( player );
	c = get_class( player );
	if ( !isdefined( g ) || !isdefined( c ) )
		return undefined;
	if ( !IS_TRUE( c.additive ) )
	{
		if ( IsSubStr( weapon.name, g.stem ) )
			return g;
		return undefined;
	}
	for ( t = 1; t <= tier( player ); t++ )
	{
		if ( isdefined( c.tiers[ t ] ) && IsSubStr( weapon.name, c.tiers[ t ].stem ) )
			return c.tiers[ t ];
	}
	return undefined;
}

function class_stems( player )
{
	stems = [];
	g = gun( player );
	if ( !isdefined( g ) )
		return stems;
	c = level.tod_classes[ player.tod_class ];
	if ( !IS_TRUE( c.additive ) )
	{
		stems[ 0 ] = g.stem;
		return stems;
	}
	for ( t = 1; t <= tier( player ); t++ )
	{
		if ( isdefined( c.tiers[ t ] ) )
			stems[ stems.size ] = c.tiers[ t ].stem;
	}
	return stems;
}

function name_is_class_stem( player, name )
{
	if ( !isdefined( name ) )
		return false;
	foreach ( s in class_stems( player ) )
	{
		if ( IsSubStr( name, s ) )
			return true;
	}
	return false;
}

// Public: is this weapon the player's class primary â€” the CURRENT tier's gun
// in any form (base, PaP, any twin variant: every variant name embeds the
// stem), or that gun's alt weapon (the bowie counts for every kill hook).
function is_class_primary( player, weapon )
{
	g = gun( player );
	if ( !isdefined( g ) || !isdefined( weapon ) || !isdefined( weapon.name ) )
		return false;
	if ( name_is_class_stem( player, weapon.name ) )
		return true;
	return ( isdefined( g.alt ) && IsSubStr( weapon.name, g.alt ) );
}
