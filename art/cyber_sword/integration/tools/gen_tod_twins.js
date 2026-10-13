#!/usr/bin/env node
// =============================================================================
// gen_tod_twins.js — batch-generate the twin-swap weapon variants for every
// gun in the CLASS TIER ladders (docs/25).
//
// Ports map 1's PROVEN gen_weapon_variant_gdt.js machinery (field sets, block
// extraction, INT-typed damage trap) into a one-shot batch. v2 (2026-08-22,
// CLASS TIERS) restructured the per-gun table into LADDERS — 4 classes x 3
// tiers — so a gun is ONE entry: where its GDT is, its asset forms, which
// variant axes (ladders) it carries, and its base tune. The tier machinery
// (DPS normalization, never-shrink clips, melee damage per tier) is computed
// here from the class's T1 gun; the GSC side (_tod_classes::register_gun +
// _tod_upgrades::twin_suffix) builds the same variant names from the same
// axis letters.
//
// AXES (the user rule 2026-08-19: any upgrade touching gun data = 3 levels):
//   f FIRE RATE   fireTime x0.92/0.84/0.76          h HANDLING  reload+swap+ADS x0.85/0.75/0.65
//   r RECOIL      kick x0.90/0.80 (2 lv)            m MAG SIZE  clipSize x1.3/1.6/1.9
//   p PENETRATION small > medium > large (2 lv)     k KNIFE SPEED meleeTime+charge -10%/Lv (5 lv)
// Variant name = <stem>[<pap suffix>]_<letter><level>...  (e.g. t9_mp5_up_f1h2,
// t9_krig6_r0m3, t9_stoner63_p1, t9_me_knife_american_k4); an axis-less gun
// has ONE base-tuned form "_b". Level-0 forms are REAL assets (they carry the
// base tune) — a player never holds the raw install asset.
//
// Emits, all idempotent (safe to re-run):
//   source_data/tod_weapon_twins.gdt      the variant weapon blocks
//   zone_source/tod_twins.zpkg            weapon, lines (+ include,tod_twins in main zone)
//   gamedata/.../zm_levelcommon_weapons.csv  variant->_up rows (keeps Pack-a-Punch working)
// and prints the REGISTRATION LEDGER (map 1 measured ~230 safe / 368 = boot
// AV, docs/21 §A) — and THROWS above LEDGER_GUARD.
//
// ONE GUN PER BUILD: flip a ladder entry's `enabled` to true, regenerate,
// build, boot-test, then the next (map 1's hard rule).
// =============================================================================

'use strict';

const fs = require('fs');
const path = require('path');

const REPO = path.join(__dirname, '..');
const TOOLS = 'C:/BO3Tools/TOD2Cybercity';
const OUT_GDT = path.join(REPO, 'source_data', 'tod_weapon_twins.gdt');
const OUT_ZPKG = path.join(REPO, 'zone_source', 'tod_twins.zpkg');
const CSV = path.join(REPO, 'gamedata', 'weapons', 'zm', 'zm_levelcommon_weapons.csv');

// ---- field sets (verbatim from map 1's proven tool) ------------------------
const RECOIL_KEYS = new Set([
  'hipGunKickPitchMin', 'hipGunKickPitchMax', 'hipGunKickYawMin', 'hipGunKickYawMax',
  'adsGunKickPitchMin', 'adsGunKickPitchMax', 'adsGunKickYawMin', 'adsGunKickYawMax',
  'hipViewKickPitchMin', 'hipViewKickPitchMax', 'hipViewKickYawMin', 'hipViewKickYawMax',
  'adsViewKickPitchMin', 'adsViewKickPitchMax', 'adsViewKickYawMin', 'adsViewKickYawMax',
]);
const FIRE_KEYS = new Set(['fireTime', 'holdFireTime', 'introFireTime']);
const RELOAD_KEYS = new Set([
  'reloadTime', 'reloadEmptyTime', 'reloadAddTime', 'reloadEmptyAddTime',
  'reloadStartTime', 'reloadStartAddTime', 'reloadEndTime',
  'reloadQuickTime', 'reloadQuickEmptyTime', 'reloadQuickAddTime', 'reloadQuickEmptyAddTime',
]);
const SWAP_KEYS = new Set([
  'raiseTime', 'firstRaiseTime', 'altRaiseTime', 'quickRaiseTime', 'emptyRaiseTime',
  'dropTime', 'emptyDropTime',
]);
// ADS transition — folded into HANDLING (user 2026-08-19 "add ADS to handling")
const ADS_KEYS = new Set(['adsTransInTime', 'adsTransOutTime']);
// Melee swing speed — map 1's ballistic Berzerker recipe (meleeTime/meleeChargeTime)
// meleeLeftTime (2026-09-26): the gauntlet's left hook, scaled with its right; 0 on every other blade.
const MELEE_KEYS = new Set(['meleeTime', 'meleeLeftTime', 'meleeChargeTime']);

// NO MELEE LUNGE, ROSTER-WIDE (user 2026-08-23: "Remove the lunge swing from
// all melee. It makes them inconsistent").
// meleeLungeRange is the automatic step-toward-the-target the engine adds to a
// swing. It was never set here, so each blade inherited whatever its port
// shipped — and they disagreed: Combat Knife 100, Wakizashi 70, Stormbreaker 0.
// Three blades, three different reach-on-swing behaviours, which is exactly the
// inconsistency the user felt: the same swing at the same distance connects on
// one tier and whiffs on the next. Forcing 0 makes every blade's reach purely
// its own meleeRange, so a promotion changes damage and speed and NOTHING about
// where the swing lands. Guns already ship 0, so this only ever touches melee.
// Applied as a str override (meleeLungeRange is quoted in the GDT) inside
// baseTune, which every form AND every k-ladder twin passes through.
// *** meleeChargeRange IS THE LUNGE. meleeLungeRange ALONE DOES NOTHING. ***
// 2026-08-23, second attempt. The first pass zeroed only meleeLungeRange and the
// user still lunged with the combat knife. The field that actually drives the
// charge-toward-target on a swing is meleeChargeRange, and MAP 1 ALREADY PROVED
// IT: its LIVE leviathanaxe.gdt carries meleeChargeRange "0" while the pristine
// pack copy — the one THIS generator reads as its source — still has "100".
// So the axe was fixed over there and our roster never inherited it.
// Both fields are zeroed here: meleeChargeRange kills the lunge, meleeLungeRange
// is kept at 0 for consistency (it was the roster's other inconsistency — knife
// 100 / wakizashi 70 / stormbreaker 0).
// Do NOT also zero meleeChargeTime / meleeChargeDelay: those are the swing's own
// animation timing, map 1 left them alone, and the k-ladder scales meleeTime.
const MELEE_NO_LUNGE = { meleeLungeRange: '0', meleeChargeRange: '0' };
// RESERVE +30% ON EVERY GUN (user 2026-08-23: "all guns need a reserve increase
// by 30%"). maxAmmo/startAmmo are in MAGAZINES (see the PaP note below), so
// x1.3 is rounded to whole mags by scaleSets (INT_KEYS). Applied in baseTune's
// base pass ONLY: the _up form copies maxAmmo/startAmmo verbatim from the
// TUNED base (PAP_COPY_KEYS, computePapSet), so every PaP form inherits the
// bump without a second scale; ladder variants never touch these keys; melee
// forms carry 0 and scaleSets keeps 0. The three ported SIDEARMS are not
// generated here — their install-side GDTs get the same x1.3 by hand (same
// rounding), see CHANGELOG v9.36.
// 1.3 -> 1.4 (user 2026-08-23: "increase reserve of all guns from 30% to 40%").
// THREE DOWNSTREAM EFFECTS, checked before changing it:
//  1. IT MULTIPLIES WITH CLASS_RESERVE_MULT, it does not replace it. Skirmisher
//     goes 1.3x1.3 = 1.69x -> 1.4x1.3 = 1.82x. That is intended: the class knob
//     was defined as "on top of global", so raising global raises it too.
//  2. SCAVENGER (the "reserve" upgrade domain) does NOT compound. It is a KILL
//     REFUND — one round per N kills — not a multiplier, so it cannot stack
//     multiplicatively here. It only gains headroom, because a refund is capped
//     by maxAmmo. Beneficial and bounded.
//  3. THE TWO REMAINING HAND-TUNED SIDEARMS FALL 7.7% BEHIND. t9_magnum and
//     t9_amp63 are NOT generated here — their reserves were multiplied by 1.3 by
//     hand in the mod-tools GDTs. They stay at 1.3 while everything else moves to
//     1.4. DELIBERATELY NOT FIXED: those GDTs live outside this repo and are
//     SHARED WITH MAP 1, so editing them would silently change that map's guns
//     too. 7.7% on a sidearm nobody empties is the cheaper error. (The Bulldog is
//     no longer in this group — v10.8 made it a generated variant, so it tracks
//     the multiplier automatically.)
// maxAmmo/startAmmo are counted in MAGAZINES and INT-rounded, so a small gun may
// not move at all while a large one gains a whole magazine.
// 1.4 -> 1.0 (user 2026-08-24: "Now that we have ammo crates lets reduce the
// ammo reserve constant ... we can just remove that now"). The global buff
// existed because this map has NO mystery box and NO wallbuys, so the reserve
// was the only ammo in the game. The breather AMMO CRATES (5,000, four of them,
// _tod_ammo_crate.gsc) are now that supply, so carried ammo goes back to the
// ports' own values and the crates become the answer to running dry.
// EFFECT: every gun loses ~29% of its carried rounds. The skirmisher keeps its
// own CLASS_RESERVE_MULT 1.3 (that knob is a decision about the SMG line and is
// unrelated to this one), so it lands at 1.3x source rather than 1.82x.
const RESERVE_MULT = 1.0;
const RESERVE_KEYS = new Set(['maxAmmo', 'startAmmo']);

// +1 MAGAZINE ON EVERY GUN (user 2026-08-26: "all guns need to have 1 extra mag.
// Ammo is scarce even when we have an ammo crate. Many people are complaining").
//
// ADDITIVE, AND THAT IS THE WHOLE POINT. RESERVE_MULT is a ratio, and the
// 2026-08-23 pass above already recorded why a ratio is the wrong tool for this
// job: "a small gun may not move at all while a large one gains a whole
// magazine". Reserves here run from 2 magazines (Death Machine) to 24 (RPG), so
// any x-factor big enough to help the Death Machine hands the RPG a fistful of
// rockets. One flat magazine lands identically on both — which is exactly what
// "all guns need 1 extra mag" asks for.
//
// APPLIED AFTER the multiplicative pass — final = round(src x mults) + 1 — so it
// composes with CLASS_RESERVE_MULT and gun.reserveMult rather than being scaled
// by them. The skirmisher still gets its x1.3 AND the magazine.
//
// FOUR THINGS CHECKED BEFORE ADDING IT:
//  1. MELEE IS SAFE. Every blade form carries maxAmmo/startAmmo 0, and addSets
//     keeps 0 the same way scaleSets does. A knife must never be handed a
//     magazine, and the 0-guard is the only thing standing between it and one.
//  2. THE PaP FORM INHERITS IT FOR FREE, so do NOT add it again in the isUp
//     branch. computePapSet reads the TUNED base and maxAmmo/startAmmo are
//     PAP_COPY_KEYS (factor 1), so every _up form copies the already-bumped
//     value. A second add there would silently give PaP guns two magazines.
//  3. papKeepSource IS THE ONE EXCEPTION AND IT IS HANDLED IN baseTune. That
//     branch bypasses papApply outright, so the Magnum's _up form would have
//     been the only asset in the map to miss the magazine. The 2026-08-25 note
//     there deliberately keeps RESERVE_MULT and the class knob out of that
//     branch because they were silent balance changes to a gun nobody asked to
//     retune — this one is a roster-wide change the user asked for by name, so
//     it goes in, and the note now says so.
//  4. THE AMMO CRATE GAINS WITH IT. The crate refills to maxAmmo, so raising
//     maxAmmo raises what 5,000 points actually buys. That is the second half of
//     the complaint ("even when we have an ammo crate") and it is why this knob
//     answers it and a crate price cut would not have.
//
// NOT COVERED — the two secondaries that are not generated here: `pistol_standard`
// (heavy T1) and `t9_amp63` (slasher T1). Their GDTs are install-side and SHARED
// WITH MAP 1, so editing them would silently change that map's guns too — the
// same call the v9.36 and v10.x reserve passes made. Both are T1 SIDEARMS, never
// a class primary, so no player's main gun misses the magazine.
const RESERVE_ADD = 1;

// ---- PER-CLASS TUNING (user 2026-08-23, after the full playthrough) ---------
// "We need a buff on the skrimisher class. Mostly all around ammo pgrade by 30%
// on reserve for all skirmisher guns ... Damage on all skirmisher can get buffed
// by 10%."
//
// THESE STACK ON TOP OF THE GLOBAL PASS, deliberately and on the user's explicit
// confirmation ("Yes 30% on top of global"). RESERVE_MULT 1.3 already applies to
// every gun in the map, so a skirmisher gun ends at 1.3 x 1.3 = 1.69x its GDT
// reserve. Keeping the two as separate knobs rather than baking 1.69 into
// RESERVE_MULT matters: the global one is a map-wide economy decision and the
// class one is a balance decision about the SMG line, and they will move
// independently.
const CLASS_RESERVE_MULT = { necromancer: 1.3 };   // key renamed with the class 2026-09-26 (its T1 primary is gone; kept so nothing else moves)

// DAMAGE IS APPLIED TO THE TIER-1 GUN ONLY — see the guard in baseTune. T2/T3
// damage is NORMALIZED from the tuned T1 inside computeTierOverrides
// (t1.damage x TIER_DPS x fireTime/t1.fireTime), so the bump propagates up the
// ladder by construction and the 1 / 1.5625 / 2.4414 tier relationship is
// preserved exactly. Scaling the higher tiers here as well would apply it TWICE
// on them (once inherited through normalization, once directly) and quietly turn
// a +10% class buff into +21% for the MP5 and MP7.
// 1.10 -> 1.15 (user 2026-08-23: "It needs an overall damage buff by 15%").
// READ AS THE TOTAL, NOT AS A SECOND BUMP: this replaces the earlier +10%, so
// the SMG line is +15% over its raw GDT damage, not 1.10 x 1.15 = +26.5%. Say so
// if a further +15% on top was meant — it is a one-digit change either way.
// SKIRMISHER *IS* THE SMG CLASS: MAC-10 / MP5 / MP7 are its three tiers, so this
// one knob is the whole SMG roster and nothing else moves.
// HEAVY -10% (user 2026-08-24: "The LMG class needs a damage nerf by 10%").
// Same T1-ONLY rule as the skirmisher line above, and for the same reason: 0.90
// lands on the STONER's damage/minDamage, and computeTierOverrides normalizes
// the HK21 and the Death Machine from that TUNED T1 — so the whole LMG line is
// exactly -10% and the 1 / 1.5625 / 2.4414 tier spacing is preserved. Scaling
// the higher tiers here as well would compound to -19% on them.
// HEAVY 0.90 -> 0.81 (user 2026-08-24: "nerf LMG class damage overall by 10%").
// A FURTHER 10% on top of the earlier one, i.e. 0.90 x 0.90 — the LMG line now
// sits 19% below its raw port damage. Context: the armory audit put HEAVY top of
// the DPS table at every tier (T1 3,187 vs assault 2,000) while ASSAULT sat
// 33-37% below both other classes, so this closes the gap from the top.
// Still T1-ONLY — computeTierOverrides normalizes the HK21 and Death Machine
// from the tuned Stoner, so it propagates by construction.
// SKIRMISHER 1.15 -> 1.3225 (user 2026-08-25: "give the smg class gun primaries
// and secondaries 15% damage increase"). 1.15 x 1.15 — a FURTHER 15% on top of
// the existing knob, so the SMG line now sits 32.25% above its raw port damage.
//
// THIS ONE KNOB MOVES THE SECONDARIES TOO, which is why there is no second
// entry for them. Every skirmisher secondary is CAPPED rather than
// ladder-derived: computeSecondaryOverrides clamps each one to
// PRIMARY_T1[cls].dps x SEC_CAP_REL[tier], and all three sit exactly on that
// ceiling (Bulldog 1,908 DPS = MAC-10 2,981 x 0.64). PRIMARY_T1 is measured
// from the TUNED T1 primary, so raising this multiplier raises the MAC-10, the
// MAC-10 raises the ceiling, and the Bulldog / SG12 / SPAS-12 all rise with it
// by exactly the same 15%. Adding a separate secondary knob would have applied
// the buff twice.
//
// The PaP forms need nothing either: papApply derives them as tuned-base x1.25,
// so +15% on the base is +15% on the PaP by construction.
// ⚠️ v14.32 then v14.33 (user 2026-08-30: "nerf skirmisher damage by 10%.
// Primary weapons only", then "reduce damage for skirmisher primary by another
// 10%") — SKIRMISHER 1.3225 -> 1.19025 -> 1.071225. That is x0.9 TWICE, i.e.
// x0.81 of where the class started the day, NOT x0.8: the second cut is 10% of
// the already-reduced number, which is what "another 10%" means. Both were
// primaries-only, and CLASS_SEC_CAP_MULT below is pinned to an ABSOLUTE value
// rather than a ratio precisely so a second cut needs no second edit — the
// shotgun ceiling stays where it was through any number of primary retunes.
// The "PRIMARY WEAPONS ONLY"
// clause is why CLASS_SEC_CAP_MULT below exists: the paragraph above is still
// true, this knob DOES move the secondaries, and that coupling was correct for
// the 2026-08-25 buff (which was explicitly "primaries and secondaries"). It is
// WRONG here. Left alone, the MAC-10 would drop 10%, drag PRIMARY_T1 down 10%,
// and the Bulldog / SG12 / SPAS-12 would fall 10% with it — the exact guns this
// order excluded. The cap is therefore pinned at the OLD multiplier.
const CLASS_DAMAGE_MULT  = { necromancer: 1.01766375, heavy: 0.81, assault: 1.10 };   // skirmisher -5% 2026-09-03 (1.071225 x 0.95; THIRD cut - two -10% on 2026-08-30 took 1.3225 -> 1.071225); assault 1.10 = the 2026-08-29 "+10% damage buff" (user order); T1-only, tiers normalize from it
// THE MULTIPLIER THE SECONDARY CEILING IS MEASURED AT, when it must differ from
// the one the primaries ship at. computeSecondaryOverrides clamps each sidearm
// to PRIMARY_T1[cls].dps x SEC_CAP_REL[tier], and PRIMARY_T1 is measured off the
// TUNED T1 primary — so the cap normally rides CLASS_DAMAGE_MULT by
// construction. An entry here decouples the two: the cap is computed as if the
// class knob were still this value, while the primaries actually ship at
// CLASS_DAMAGE_MULT.
//
// ONLY ADD AN ENTRY FOR A KNOB THAT DELIBERATELY MOVES PRIMARIES ALONE. If a
// future order moves the whole class again, DELETE the entry rather than
// updating both numbers — an absent entry means "cap follows the primaries",
// which is the default and the safer state to fall back to. Two numbers that
// must be kept in a ratio are exactly the lockstep pair this codebase keeps
// getting burned by; this comment is the reason the ratio is not hidden in one.
// THE SKIRMISHER SIDEARM CEILING, and the pre-v17.4 baseline it is measured from.
//
// 1.3225 is the ABSOLUTE pin v14.32 introduced so the primaries' own cuts stop
// dragging the shotgun ceiling with them — which is why a secondary change is
// always a SEPARATE edit from a primary one, and why the -5% primary cut above
// does not touch these three guns.
//
// HISTORY, because this knob has now moved twice in one day and the second move
// REVERSED the first: v16.99 took it to x0.90 (1.19025) on "nerf skirmisher
// primaries by 5% and secondaries by 10%". The user played it and reversed the
// secondary half the same evening — "revert the skirmisher secondary nerf and
// instead buff by 10%. Except the spaz. That'll actually be 5% nerf instead."
// So the ceiling is now measured from the ORIGINAL 1.3225, not from the nerfed
// value: +10% for the Bulldog and the SG12, and the SPAS-12 alone lands at -5%.
const SKIRM_SEC_BUFF = 1.10;    // Bulldog + SG12: +10% on the 1.3225 baseline
const SKIRM_SPAS_NET = 0.95;    // SPAS-12 ALONE: -5% on that same baseline
const CLASS_SEC_CAP_MULT = { necromancer: 1.3225 * SKIRM_SEC_BUFF };   // = 1.45475

// SECONDARIES ARE 25% WEAKER THAN THEY SHIPPED (user 2026-08-24: "the current
// secondaries need an all around 25% nerf ... make sure they are all pretty
// weak compared to the primary slot"). ONE knob for every gun carrying
// `secondary: true`. The two RAW PORTS (pistol_standard, t9_amp63) have no GDT
// in this tree and take the same 0.75 script-side in
// _tod_upgrades::gun_balance_mult, which is the ONLY other place a secondary's
// damage is touched. Move both or neither.
//
// THIS IS THE SEAT THE COMING SEC_DPS LADDER TAKES. When secondaries go
// per-tier (4 classes x 3 tiers), the T1 rung keeps this multiplier and T2/T3
// normalize FROM the tuned T1 exactly the way CLASS_DAMAGE_MULT feeds
// computeTierOverrides — so this stays a T1-only knob and never gets applied a
// second time up the ladder.
//
// IT RE-NERFS THE BULLDOG DELIBERATELY. Its own x0.5 -> x0.75 -> removed
// history (see gun_balance_mult) was a decision about the Bulldog ALONE against
// the roster it sat in; this is a decision about the whole SECONDARY SLOT. The
// old script nerf is still gone and is not coming back — do not stack them.
//
// APPLIED IN BOTH BRANCHES OF baseTune, and it has to be. The base form takes
// it through the sets[] pass; the _up form cannot, because both of today's
// secondaries PIN their PaP damage as a literal in `tune.setUp` (the Bulldog's
// 240 so the uniform x1.25 cannot ship a PaP weaker than stock, the Magnum's
// 1750 so its headshot number does not move) and absSet writes those AFTER
// papApply. Scale only the base and the PaP forms keep their full pinned
// damage — the nerf would silently apply to exactly half of each gun.
const SECONDARY_DMG_MULT = 0.75;
// SLASHER SIDEARMS +25% ON FIVE NUMBERS (user 2026-09-01: "Pick the 5 most
// important GDT numbers and buff 5 of them by 25% for the slashers secondaries.
// All tiers base and pap"). The five: damage, fire rate (fireTime), clipSize,
// reserve magazines, reload times. ONE knob, applied per gun on the two GENERATED
// slasher sidearms (UDM T2, RK7 T3) as: tune.fire = tune.reload = 1/BUFF (the
// FIRE_KEYS / RELOAD_KEYS sets), clipMult = BUFF (sidearm clipMult lives in
// computeSecondaryOverrides), reserveMult x BUFF, and dmgMult = BUFF. WHY dmgMult
// IS EXACTLY BUFF AND NOT MORE: the T1 reference (SEC_T1_REF.slasher) already
// carries the AMP63's +25% (its script multiplier 0.75 -> 0.9375), so the
// ladder hands T2/T3 the +25% damage by construction - but the ladder holds DPS
// against the gun's OWN fireTime, and fireTime x0.8 would pull that damage back
// x0.8. dmgMult, applied AFTER the cap, restores it: final damage = +25%, final
// fire rate = +25%, so DPS is x1.5625 - the user asked per NUMBER, and that is
// the consequence, stated in the CHANGELOG. The T1 AMP63 is a RAW PORT (shared
// install-side GDT): only its DAMAGE moves (gun_balance_mult); its other four
// numbers cannot be touched from this repo - flagged to the user, not done.
const SLASHER_SEC_BUFF = 1.25;
const DAMAGE_KEYS = new Set(['damage', 'minDamage']);
// Splash damage. Deliberately NOT part of DAMAGE_KEYS: tier normalization
// derives `damage` from a DPS target and splash has no place in that math.
// But the flat SECONDARY_DMG_MULT must reach it, or a launcher secondary keeps
// 100% of the number that actually kills things while its direct hit — the
// number almost nobody lands with a rocket — takes the full -25%.
const EXPLOSION_KEYS = new Set(['explosionInnerDamage', 'explosionOuterDamage']);
// MAG SIZE as REAL twins (user 2026-08-20). clipSize ONLY. startAmmo/maxAmmo are
// counted in MAGAZINES, not rounds (krig = 8 mags x 30 = 240 reserve), so scaling
// them multiplied total ammo on top of the clip growth — the 'unlimited ammo' bug.
const MAG_KEYS = new Set(['clipSize']);
// Fields that must stay INTEGERS after scaling — clip/ammo counts (whole
// rounds) and damage (map 1's INT-typed damage trap: a float damage value
// silently reads as 0 in game).
const INT_KEYS = new Set([...MAG_KEYS, 'damage', 'damageMin', 'minDamage', 'startAmmo', 'maxAmmo']);

// ---- ladders (step tables; index = level) -----------------------------------
const FIRE_STEP = [1, 0.92, 0.84, 0.76];     // f0..f3
const HANDLING_STEP = [1, 0.85, 0.75, 0.65, 0.45]; // h0..h3, h4 = DARK -55% (MP7 PaP only, v17.10)
// RECOIL ladder. History: -25/-45/-65% (2026-08-19) -> HALVED 2026-08-21 (user:
// "nerf the recoil upgrade by like 50%") to -10/-20/-30% -> v9.45 2026-08-23
// (user: "recoil should be two levels only. 8% and 16%") to TWO levels at
// -8/-16% -> 2026-08-26 ASSAULT BUFF (user: "Recoil will go to 10% per level")
// to -10/-20%, still two levels -> v16.50 2026-09-02 (user: "buff recoil to
// 15%") to -15/-30%, still two levels. The card art + the Lua DOMAIN desc + the Lua
// DETAIL val table + add_domain's max carry these numbers — keep all of them in
// lockstep, and note that AXIS.r.levels below is the one that decides how many
// weapon assets actually get emitted (unchanged at 2, so this retune changes
// gun DATA only: same asset names, same registration count, no dead forms).
// RECOIL (v17.10, user 2026-09-04: "First level can be 20% and dark upgrade
// will be 30% at 50% improvement total. And should only be on AK 47").
//   r0 = none, r1 = the domain's ONE level (-20%), r2 = the DARK rung (-50%).
// The domain max is therefore 1, not 2 — r2 is not reachable by levelling, only
// by the dark upgrade (see twin_suffix). Was [1, 0.85, 0.70] = -15/-30 over two
// levels on all three assault guns.
const RECOIL_STEP = [1, 0.85, 0.70, 0.40];   // r0 / r1 -15% / r2 -30% / r3 DARK -60% (AK-47 PaP only, v17.10)
// KNIFE SPEED — LOGARITHMIC, not linear (user 2026-08-23, after the full
// playthrough: "The melee class needs a nerf for sure. Its mostly the melee
// swing speed and the leech HP. Maybe we can increase logorithimcally for both
// instead of linearly per level. It ends up getting crazy.").
//
// WAS [1, .9, .8, .7, .6, .5] — a flat -10%/Lv reaching HALF swing time at k5,
// which stacked with the slasher's 1.1 move speed and one-hit kills to round 14
// is the "crazy" the user means. NOW 1 - 0.10*log2(1+Lv), tabulated:
//   k0 1.00   k1 0.90   k2 0.84   k3 0.80   k4 0.77   k5 0.74
// LEVEL 1 IS DELIBERATELY IDENTICAL to the old curve (-10%) — the first point
// a player spends must feel the same as it always did; it is the TAIL that is
// cut, from -50% down to -26%. Diminishing returns is the whole idea: every
// further level still helps, none of them doubles you.
// Kept as an explicit TABLE rather than computed so the shipped numbers are
// readable here and cannot drift with a Math change.
const KNIFE_STEP = [1, 0.90, 0.84, 0.80, 0.77, 0.74, 0.54];   // k0..k5, k6 = DARK -46% swing time (Stormbreaker PaP only, v17.10)
// MAG SIZE NERFED 2026-09-01 (user: "mag size needs a nerf so should be 20% per
// tier instead of 30%"). Was [1, 1.3, 1.6, 1.9] from 2026-08-20. Same four
// m-forms, same registration count — the ledger does not move; only the
// clipSize inside each m-form changes (Math.round of base x step: the Krig's 33
// goes 40/46/53 instead of 43/53/63). Mirrors that must follow: the add_domain
// desc + Lua DOMAIN[7]/DETAIL[7] (+20/+40/+60%), the armory row, and the three
// i_tod_card_mag_size_* PNGs, which bake +30/+60/+90% as pixels (docs/65 is
// the re-bake prompt).
const MAG_STEP = [1, 1.2, 1.4, 1.6, 1.9];  // m0..m3 +20%/Lv, m4 = DARK +90% (AK-47 PaP only, v17.10)
// PENETRATION tiers (user 2026-08-21): the engine's three values are small /
// medium / large — there is no "low" (verified across the Skye pack).
const PEN_TIER = ['small', 'medium', 'large'];

// axis letter -> how a level scales a block. `sets` = [[keySet, stepTable]]
// (scaleSets); `pen` = the string-valued penetrateType ladder. The GSC side
// (_tod_classes::register_gun axes) uses the SAME letters.
const AXIS = {
  q: { domain: 'mage_quickhands', levels: 1, sets: [[new Set([...SWAP_KEYS, 'quickDropTime', 'altDropTime', 'adsAltDropTime', 'adsAltRaiseTime', 'swimDropTime']), [1, 1 / 3]]] },
  f: { domain: 'firerate',    levels: 3, sets: [[FIRE_KEYS, FIRE_STEP]] },
  h: { domain: 'handling',    levels: 3, sets: [[RELOAD_KEYS, HANDLING_STEP], [SWAP_KEYS, HANDLING_STEP], [ADS_KEYS, HANDLING_STEP]] },
  r: { domain: 'recoil',      levels: 2, sets: [[RECOIL_KEYS, RECOIL_STEP]] },   // v9.45: 3 -> 2 (user)
  m: { domain: 'magsize',     levels: 3, sets: [[MAG_KEYS, MAG_STEP]] },
  k: { domain: 'knifespeed',  levels: 5, sets: [[MELEE_KEYS, KNIFE_STEP]] },
  p: { domain: 'penetration', levels: 2, pen: true },
  // PELLETS (2026-09-26, the Breacher, user: "they should have pellets ... as one of
  // their upgrades", ~+20%/Lv). NOT a scale step: level N ADDS gun.pellets[N] to
  // shotCount on every form (base + PaP), per gun, because a 3-pellet Mozambique
  // cannot take +20% steps without a dead level. The sustained pin reads level 0.
  e: { domain: 'pellets', levels: 3, pellets: true },
};

// ---- BASE OVERRIDES (user 2026-08-21) --------------------------------------
// Tuning that must apply to the gun ITSELF, not to an upgrade level: every
// gun's moveSpeedScale forced to 1.0, a +15% recoil bump across the roster,
// +20% ADS time, and per-gun clip/rate tunes.
//
// WHY THIS IS A TWIN AND NOT A GDT EDIT: the Skye GDTs live in the shared tools
// root and map 1 ALREADY rewrites their moveSpeedScale. Editing them here would
// silently retune map 1's guns.
//
// WHY MOVE SPEED MUST BE 1.0: the weapon's own moveSpeedScale MULTIPLIES with
// the player scale our class system sets, so a 0.95 gun made HEAVY really run
// at 0.8 x 0.95 = 0.76 — a hidden second penalty. With guns at 1.0,
// class_speed_base() is the single owner of move speed (user's call).
const RECOIL_BUMP = 1.15;              // +15% kick on every gun (user 2026-08-21)
const KRIG_RECOIL_BUMP = 1.5625;       // krig ONLY: kick on top of the roster bump
                                       // (1.25 -> 1.5625, user 2026-08-21, two passes of
                                       // "nerf the krig recoil by another 25%") -> x1.797 stock
const ADS_BUMP = 1.20;                 // ADS in/out TIME +20% = slower ADS, a deliberate
                                       // mobility nerf across every gun including the knife
// KRIG CLIP 25 (user 2026-08-21, was 30). RETIRE IT when the Krig becomes the
// assault T2 gun (user 2026-08-22 #7: "tier-2 clips smaller than tier-1 — fix
// this") — set KRIG_CLIP = undefined in that build; the never-shrink rule
// (CLIP_STEP) then lifts it to round(Enfield 30 x 1.10) = 33.
const KRIG_CLIP = undefined;           // RETIRED 2026-08-22 (Phase 2b): the Krig is assault T2 now; the
                                       // never-shrink rule sets its clip from the Enfield (30 x 1.10 = 33)
// KRIG RATE OF FIRE -> 600 rpm (user 2026-08-21). Stock fireTime is 0.092
// (652 rpm) and 600 rpm is 0.1s, so this is applied as a RATIO.
const KRIG_FIRE_SCALE = 0.1 / 0.092;
const STONER_CLIP = 60;                // Stoner base magazine -20%, was 75 (user 2026-08-21)

// ---- NAIL GUN NERF (user 2026-09-09) --------------------------------------
// "The nail gun base and pap need a 15% damage nerf and 10% fire rate nerf and
// clip nerf by 25%."
//
// ONE SET OF KNOBS COVERS BOTH FORMS. computePapSet builds the _up block from
// the TUNED BASE (x PAP_UP on damage/clip, x PAP_FAST on fireTime), so a base
// nerf propagates to the PaP form by construction -- which is why there is no
// tune.setUp here and must not be one. Proof it derives rather than ships its
// own numbers: the pre-nerf pair was 460/575 damage (x1.25), 0.157/0.1256
// fireTime (x0.8) and 40/50 clip (x1.25), exactly the PaP factors.
//
// RATE: fireTime is an INTERVAL, so "10% fewer shots per second" is x1/0.9, not
// x0.9. Same convention as the ice staff's 0.80 -> 1.00 (20% fewer shots).
const NAIL_RATE_NERF = 1 / 0.90;
// DAMAGE: the number the user asked to see move, applied to the SHIPPED value.
const NAIL_DMG_NERF  = 0.85;
// ⚠️ THE FIRE-RATE NERF WOULD OTHERWISE CANCEL THE DAMAGE NERF. A secondary's
// damage is NOT the port's -- computeSecondaryOverrides normalizes it to a DPS
// target held against the gun's OWN fireTime (round(2929.6875 x fireTime) for
// this rung), so slowing the gun 10% RAISES its normalized damage by the same
// 10% before dmgMult ever runs. Divide that back out, or the two instructions
// fight and the gun ships at 0.944 damage instead of 0.85. This is the same
// trap the PaP +25% case documents at CLASS_DAMAGE_MULT: the ladder holds DPS,
// so anything that moves fireTime must pay the difference back explicitly.
const NAIL_DMG_MULT  = NAIL_DMG_NERF * 0.90;   // = 0.765, i.e. 0.85 / NAIL_RATE_NERF
// CLIP: applied to the tuned base; the PaP clip derives from it.
const NAIL_CLIP_NERF = 0.75;

// ---- HIT-LOCATION MULTIPLIERS: NORMALIZED ACROSS THE ROSTER ---------------
// USER RULE (2026-08-21): "headshot multiplier needs to be 3x for all guns ...
// NO GUNS SHOULD VARY UNLESS I EXPLICITLY SAY SO." The ports ship these wildly
// uneven (mp5 3.0 / krig 6.0 / stoner 5.0 / enfield 5.0 / hk21 torso 2.0 ...).
// Helmet mirrors the head, neck is head-adjacent -> all three 3.0; every other
// body zone 1. Differentiation comes ONLY from the HEADSHOT upgrade domain.
// LOC_NORM only names the four keys every port already agreed on. LOC_FLAT is
// the REST of the hit-location table — every port in the roster ships these at
// 1 already, so they never needed setting until the Magnum arrived with 2.0
// limbs and a 4.0 torso-mid. Applied only where a gun asks for it.
const LOC_FLAT = {
  locTorsoMid: 1, locTorsoLower: 1,
  locLeftArmLower: 1, locLeftArmUpper: 1, locLeftFoot: 1, locLeftHand: 1,
  locLeftLegLower: 1, locLeftLegUpper: 1,
  locRightArmLower: 1, locRightArmUpper: 1, locRightFoot: 1, locRightHand: 1,
  locRightLegLower: 1, locRightLegUpper: 1,
};

const LOC_NORM = {
  locHead: 3.0,
  locHelmet: 3.0,
  locNeck: 3.0,
  locTorsoUpper: 1,
};

// ---- CLASS TIERS (docs/25 §6) ------------------------------------------------
// A tier's BASE form is "about as strong as the PaP'd version" of the tier
// below — in DPS. PaP is +25% damage AND +25% fire rate, so a PaP form is
// x1.5625 the DPS of its base; therefore T2 base = T1 base x1.5625 (= T1 PaP
// DPS) and T3 base = T2 PaP DPS = x1.5625^2 = x2.4414. (The first cut used
// x1.25 / x1.5625 — damage-only — which made every promotion a DPS DOWNGRADE
// until the new gun was PaP'd again; caught by the user 2026-08-22.)
// Applied to DAMAGE (minDamage keeps the port's own min/max ratio) at the
// gun's OWN fire time — the port keeps its feel. Only computed when the
// class's T1 gun is ENABLED.
const PAP_DPS = 1.25 * 1.25;                       // damage x rate
const TIER_DPS = [0, 1, PAP_DPS, PAP_DPS * PAP_DPS];   // 1 / 1.5625 / 2.4414
// A promotion never shrinks the magazine (user 2026-08-22 #7): each tier's
// clip >= round( previous tier's tuned clip x CLIP_STEP ).
const CLIP_STEP = 1.10;

// ---- THE SECONDARY LADDER (user 2026-08-24) --------------------------------
// "every tier for every class needs its own secondary ... each teir of
// secondsries will get better just like the primaries do". SAME steps as the
// primary ladder on purpose: reusing TIER_DPS means a secondary sits at a
// CONSTANT fraction of its class's primary at every tier, so "pretty weak
// compared to the primary slot" holds at T1 and still holds at T3 without a
// second knob to keep in sync. Split them only if the gap should CHANGE as you
// climb, which is not what was asked for.
const SEC_DPS = TIER_DPS;

// ---- THE CEILING: A SECONDARY MAY NOT BEAT THE PRIMARY ONE TIER BELOW -------
// (user 2026-08-24, after an audit of the shipped numbers: "These secondaries
// should not be competing with primary guns in DPS. I would say maybe the
// secondaries should be comparable to the primary of the tier below.")
//
// The audit was right and the margin was not subtle — measured on the build
// that shipped, every skirmisher sidearm sat at 1.86x its OWN SAME-TIER primary
// and every assault one at 1.63x. The tier-2 SG12 alone did 8,625 DPS against
// the MAC-10's 2,981.
//
// So each secondary tier is capped at the DPS of the primary ONE TIER BELOW it:
//   sec T2 <= primary T1     sec T3 <= primary T2
// Tier 1 has no primary below it, so the ladder is extended one step DOWN by
// the same ratio it climbs: 1 / PAP_DPS = 0.64 x primary T1. That is a choice,
// not a measurement — it is the only rung the user's rule does not name.
const SEC_CAP_REL = [0, 1 / PAP_DPS, 1, PAP_DPS];

// CEILING, NOT TARGET (user's explicit pick over "every secondary moves to the
// rule"). Only guns ABOVE the cap come down; guns already under it are left
// exactly where they are, so this nerfs the skirmisher and assault lines and
// does not touch heavy or slasher.
//
// THE BASELINE IS THE EXISTING SECONDARY LADDER, AND IT HAS TO STAY. "Already
// under the cap, so leave it alone" is only true relative to what the gun
// CURRENTLY SHIPS — which is the SEC_DPS ladder value, not the raw port number.
// Delete that ladder and call the cap the whole rule and the under-cap guns
// fall back to their port damage: the Klauser would ship at 15 and the RPG at
// 5,250. The two passes compose — ladder first, then clamp.
const SEC_CAP_ONLY = true;

// Measured primary T1 per class, filled in by computeTierOverrides — the thing
// the cap is computed FROM. { dps } only; the caller supplies its own fireTime
// and shotCount when converting a DPS target back into a damage number.
// Every class has one, INCLUDING the melee slasher, so unlike SEC_T1_REF below
// there is nothing declared here and nothing to keep in sync by hand.
const PRIMARY_T1 = {};

// T1 REFERENCE DPS PER CLASS — what T2/T3 are normalized FROM.
//
// Two of the four T1 secondaries are GENERATED twins and are MEASURED like any
// primary T1 (skirmisher Bulldog, assault Magnum) — they are absent from this
// table for that reason. The other two are RAW PORTS the map hands out as-is,
// so there is no tuned block to measure and their reference is DECLARED here:
//
//   slasher  t9_amp63        READ from skye_t9_amp63.gdt (damage 135,
//                            fireTime 0.092) times the 0.9375 script mult in
//                            gun_balance_mult = 126.5625 (0.75 -> 0.9375 in v16.12,
//                            the slasher-sidearm +25%). Measured once, by hand,
//                            2026-08-24 — re-read it if that GDT ever moves.
//   heavy    pistol_standard NOT MEASURABLE AT ALL. The MR6 is stock and its
//                            GDT is not in this tools tree, so its ~25 base
//                            damage times the x7.2 script multiplier (180) and
//                            its fire time are both DECLARED, not read. This is
//                            the one number in the whole ladder nobody can
//                            verify from a file; treat the heavy secondary line
//                            as hand-tuned and judge it by play, not by the log.
//                            The moment the MR6 is replaced by a twinned gun,
//                            delete this row and let it be measured.
// `shot` = shotCount, the projectiles per trigger pull. It is part of the
// reference because `damage` in a GDT is PER PROJECTILE: a shotgun's 250 is
// 250 x 8 pellets on target, a revolver's 250 is 250. Both raw-port T1s here
// are single-projectile, so both are 1 — but state it, because the moment one
// of them is replaced by a shotgun an omitted 1 becomes an 8x error that
// nothing in the log would flag.
const SEC_T1_REF = {
  slasher: { damage: 135 * 0.9375, fireTime: 0.092, shot: 1 },   // v16.12: 135 x 0.9375 = 126.5625 (was 101 = 135 x 0.75); tracks gun_balance_mult
  heavy:   { damage: 180, fireTime: 0.150, shot: 1 },
};

// Melee has no DPS: damage per tier [base, PaP]. The knife keeps its shipped
// 1700/20000 (user 2026-08-21, exempt from the uniform PaP rule); each step
// doubles so a tier buys ~7 more one-shot rounds (zombie HP x1.1/round).
// MUST STAY IN LOCKSTEP with register_melee_dmg() in _tod_classes.gsc — this
// value drives the ASSET's meleeDamage, that one drives DoDamage. Retuned
// 2026-08-23 from 1700/20000, 20000/40000, 40000/80000: the old first step was
// a x11.8 jump (knife PaP == katana base), so a PaP'd tier-1 knife already
// one-hit to round 38. Now a clean x2 ladder, tier N base = tier N-1 PaP,
// mirroring the gun rule. See the comment block at _tod_classes.gsc for the
// one-hit-reach table this was tuned against.
// STORMBREAKER -15% (user 2026-08-24: "Storm breaker needs an all around nerf
// by like 15%"). Tier 3 only: 8000/16000 -> 6800/13600, base and PaP alike, so
// the axe is 15% weaker in every form it can be held in. One-hit reach against
// this map's HP curve drops storm r29 -> r28 and PaP r36 -> r35.
// KNOWN AND ACCEPTED: this is the one rung that now breaks the "tier N base =
// tier N-1 PaP" ladder — the katana's PaP (8000) out-damages a fresh
// Stormbreaker (6800) until the axe is PaP'd. That is a ~1-round dip in one-hit
// reach, not the x11.8 cliff the ladder was built to kill, and it is the direct
// consequence of nerfing the top rung alone.
// MELEE -20% ACROSS THE BOARD (user 2026-08-30: "nerf damage on melee by 20%").
// Applied to EVERY rung, base and PaP alike, so the ladder's shape is unchanged
// and only its height moves: 2000/4000 -> 1600/3200, 4000/8000 -> 3200/6400,
// 6800/13600 -> 5440/10880. Against this map's HP curve (~x1.1/round) a x0.8
// damage cut is worth ~2 rounds of one-hit reach at every rung, so the top form
// (PaP Stormbreaker) stops one-hitting around r33 instead of r35. BACKSTAB
// follows automatically (BACKSTAB_MULT x1.5 of these numbers), so the map's
// backstab ceiling drops 20400 -> 16320 with no second edit.
// LOCKSTEP: register_melee_dmg() in _tod_classes.gsc carries the same six
// numbers and must move with this line.
const MELEE_TIER_DMG = { 1: [1600, 3200], 2: [3200, 6400], 3: [5440, 10880] };

// BACKSTAB (user 2026-08-24: "BACKSTAB DAMAGE IS COMPLETELY UN-NORMALIZED
// ACROSS THE BLADES"). meleeFromBehindDamage came straight off each port and
// was incoherent in three separate ways:
//     knife       2,000 front / 1,700 behind   <- backstab WEAKER than a frontal hit
//     knife PaP   4,000 front / 20,000 behind  <- a TIER 1 weapon's 5x one-shot
//     wakizashi   4,000 / 1,700                <- backstab less than half a frontal hit
//     stormbreaker 6,800 / 0 and PaP 13,600 / 0 <- the TOP blade had none at all
// so the T1 PaP knife out-backstabbed the T3 Stormbreaker by infinity, and two
// of the six forms punished the player for flanking.
//
// DERIVED FROM MELEE_TIER_DMG, never authored: a uniform x1.5 of whatever that
// form's frontal damage is. That keeps the bonus a real mechanic (flanking is
// the slasher's only positioning skill) while making it monotonic up the ladder,
// and it stays in lockstep automatically the next time the tier damages move.
//
// x1.5 SPECIFICALLY so the map's backstab CEILING DOES NOT RISE: the highest
// backstab in the game today is the PaP knife's 20,000, and the highest after
// this is the PaP Stormbreaker's 20,400 — the same number, moved onto the
// weapon that should own it. One knob if you want a bigger or smaller bonus.
const BACKSTAB_MULT = 1.5;
// Registration ledger: every `weapon,` line the map links.
//
// GUARD RAISED 200 -> 220 (2026-08-23) to pay for ASSAULT AXIS PARITY: r + m on
// all three assault guns is 3 x 32 = 96 registrations (was 46), landing the
// real ledger at 216. Map 1 shipped a BOOTING .ff carrying 229 weapon assets
// total (docs/21 §A: "the total table, twins + base + PaP + stock cooked WWs")
// and its measured wall sits between 230 (booted) and 368 (crashed) — so 216
// total is under a known-good TOTAL, with ~14 of margin.
// DO NOT RAISE THIS AGAIN to buy a THIRD axis on any gun: axes MULTIPLY, so a
// third axis on a 2-axis gun costs +64 by itself (the skirmisher's f/h/m would
// need 384). Buy budget back by retiring an axis instead.
// RAISED 220 -> 223 (2026-09-01) TO THE FIGURE THE MAP ALREADY SHIPS AT, NOT
// FOR HEADROOM. v14.17's nine BO7 perk-can weapons took the fixed count 21 -> 30
// and the ledger 214 -> 223; every build since has BOOTED at 223 (v14.17 through
// v16.5). Once the 2026-09-01 tooling fix moved this throw above the writes, the
// generator could no longer regenerate EVEN THE UNCHANGED ROSTER — the first
// weapon retune after it (Death Machine spinMinigunOnADS, nail gun explosion)
// hit the hard stop with ZERO registrations added. 223 = zero net headroom: the
// next weapon,line ADDED anywhere (a gun, an axis, a can) trips it again, and
// must be paid for by retiring one — the rule above stands.
// v16.63 (2026-09-02): 224. The RIOT SHIELD upgrade's Lv5 form is Logical's
// standalone weapon def (weapon,log_riotshield_zm in the main zone) — ONE new
// registration, the first since the perk cans, paid for deliberately: the
// alternative (five per-level shield assets) was five, and the base shield
// (stock zod_riotshield) costs nothing because its CSV row is the inclusion lane.
// Map 1 booted at 229; 224 leaves five under that and the rule above still
// stands for the NEXT one.
// v17.10 (2026-09-04): 229, RAISED DELIBERATELY AND AS AN EXPERIMENT.
// The user restored the r axis to the Enfield and Krig 6 on top of the four
// dark rungs, which lands the ledger on exactly 229 — the figure map 1's .ff
// actually PACKED AND BOOTED (old repo docs/21 §A). So this is not new ground;
// it is the known-good line with zero margin.
//
// WHAT IS AND IS NOT KNOWN, because the difference matters here: the measured
// points are 230 twins BOOT, 368 CRASH, 414 CRASH. Everything from 231 to 367
// is UNTESTED — a 137-wide unknown band, not a gentle slope. ~230 is a floor of
// confidence, not a ceiling of capacity, and the failure is a boot AV that
// takes the whole map load down rather than degrading.
//
// ✅ BOOT-CONFIRMED 2026-09-04 — zm_tod2_cybercity loads at ledger 229 with its
// OWN asset mix, not map 1's. That is a THIRD measured point and the first on
// this map: 229 (this map, boots) / 230 (map 1 twins, boots) / 368 (boot AV).
// The untested band is now 231..367 and the rule below is unchanged — the next
// weapon,line anywhere must still be paid for by retiring one, because 229 is
// the line with ZERO margin, not a budget with room in it.
//
// ORIGINAL NOTE: 229 needs a BOOT TEST, not just a green build. If it boots, this is the
// proven line and the old rule stands — the next weapon,line anywhere must be
// paid for by retiring one. If it does not, drop the r axis from the Enfield
// and Krig again (one edit each here and in _tod_classes.gsc) for 197.
// 229 -> 232 (2026-09-07): the MAGE's three BASE staff rungs, +1 each.
//
// THIS IS THE USER'S CALL AND IT IS AN EXPERIMENT, NOT A KNOWN-SAFE NUMBER:
// *"Let's see what happens if we go to two thirty. If it crashes, then
// I'll try to make room for you."* ~230 is the last count this engine is
// KNOWN to have booted (map 1); it is NOT the proven break point, and the
// failure mode above the real ceiling is a boot-time AV, not a script
// error. If the map fails to load, this is the first thing to move --
// retire weapon rungs (the four dark rungs free 10) rather than raising it.
const LEDGER_GUARD = 235; // User-authorized Quick Hands experiment: three extra staff variants.

// THE FIXED COUNT USED TO BE A HARDCODED 15 AND IT ROTTED (caught 2026-08-23):
// the six per-class secondaries (v9.29) and the AMP63 dual-wield `ldw` half
// (v9.29a) were zoned without anyone bumping it, so the tool under-reported by
// 7 and the guard was not guarding — at the old 200 the true figure was already
// 216 with the ledger printing green. It is COUNTED now: the main zone plus
// every zpkg it `include,`s, minus our own generated output (those are
// `total`). Nothing left to keep in sync.
function countFixedRegistrations() {
  const ZONE_DIR = path.join(REPO, 'zone_source');
  const mainZone = path.join(ZONE_DIR, 'zm_tod2_cybercity.zone');
  const files = [mainZone];
  const zoneText = fs.readFileSync(mainZone, 'utf8');
  for (const m of zoneText.matchAll(/^include,(\S+)\s*$/gm)) {
    const f = path.join(ZONE_DIR, m[1] + '.zpkg');
    if (path.resolve(f) === path.resolve(OUT_ZPKG)) continue;   // our own output
    if (fs.existsSync(f)) files.push(f);
    else console.warn(`  ledger: include,${m[1]} has no .zpkg — not counted`);
  }
  let n = 0;
  const detail = [];
  for (const f of files) {
    const c = (fs.readFileSync(f, 'utf8').match(/^weapon,/gm) || []).length;
    if (c) detail.push(`${path.basename(f)} ${c}`);
    n += c;
  }
  console.log(`  ledger: fixed registrations = ${n}  (${detail.join(', ')})`);
  return n;
}

// ---- PACK-A-PUNCH = BASE +25% ACROSS THE BOARD (user 2026-08-21) -----------
// The _up asset keeps its own model/fx/camo lines; every TUNED stat is
// overwritten with the tuned base's value made 25% better:
//   bigger-is-better  x1.25 : damage, damageMin/minDamage, clipSize, meleeDamage
//   fire times        /1.25 : fireTime family (= +25% rpm)
//   smaller-is-better x0.75 : reload, swap, ADS, recoil, melee-swing times
//   copied verbatim    x1   : maxAmmo/startAmmo (reserve is in MAGAZINES),
//                             moveSpeedScale (class owns speed, stays 1.0),
//                             hit-location multipliers (never out-multiply base)
// Variant ladders compose ON TOP of the papped values.
const PAP_UP   = 1.25;        // damage/clip multiplier (+25%)
const PAP_FAST = 1 / 1.25;    // fire-time divisor (+25% rate)
const PAP_TRIM = 0.75;        // time/kick reduction (-25%)
const PAP_COPY_KEYS = new Set(['maxAmmo', 'startAmmo', 'moveSpeedScale',
  'locHead', 'locHelmet', 'locNeck', 'locTorsoUpper']);
// v2 (2026-08-22): `minDamage` (the Skye field; `damageMin` never existed)
// joins the +25% rule — the port's own PaP falloff floors were arbitrary
// (the MAC-10's doubled, the MP7's +86%), and "every gdt stat" was the order.
const PAP_UP_KEYS   = new Set(['damage', 'minDamage', 'clipSize', 'meleeDamage']);

// =============================================================================
// THE LADDERS (user-locked 2026-08-22):
//   SKIRMISHER  MAC-10 -> MP5 -> MP7        ASSAULT  Enfield -> Krig 6 -> AK-47
//   HEAVY       Stoner 63 -> HK21 -> Death Machine
//   SLASHER     Combat Knife -> katana (port pending) -> STORMBREAKER (Leviathan)
// `enabled`: emitted or not (ONE GUN PER BUILD). The four shipped guns are on.
// `forms`: [base, pap] source assets + the variant NAME builder (asset ids may
//   carry a trailing _zm the engine strips — the knife/enfield-PaP/leviathan
//   do; the suffix goes BEFORE it). `up` marks the PaP form.
// `axes`: the variant letters, outermost first (the GSC registers the same).
// `tune`: per-gun base overrides on top of the parity pass.
// `csv`: the weapon-table row (cost / VO / class; melee rows differ).
// =============================================================================
const T9 = (f) => path.join(TOOLS, 'source_data', f);

// ---- HELLBOUND DONORS (TOD II, 2026-09-20, docs/153) ------------------------
// Snapshot source GDTs the sibling map authored; see donor_gdt/README.md.
const HB = (f) => path.join(REPO, 'donor_gdt', 'hellbound', f);
// T7 pack donors (the Warrior's Dragon Gauntlet, 2026-09-26): the snapshot is
// read here; the SAME file must sit in the root source_data so gdtdb converts
// its clips / meshes / materials (t7Preflight below).
const T7 = (f) => path.join(REPO, 'donor_gdt', 't7', f);
const T7_TOOLS_GDTS = ['wpn_t7_zmb_dlc3_gauntlet_dragon.gdt'];
// The clones reference model / animation / material / image ASSETS that live
// only in the Hellbound GDTs installed at the tools root by that repo's sync.
// A missing file here is a linker "asset not found" an hour later — say it now.
const HB_TOOLS_GDTS = ['hb_saug.gdt', 'hb_car_progression.gdt', 'hb_car_base_models.gdt',
                       'hb_car_base_motion.gdt', 'hb_apex_mythic_models.gdt',
                       'hb_apex_mythic_motion.gdt', 'hb_apex_mythic_weapons.gdt',
                       'hb_r99.gdt', 'hb_r99_quality.gdt', 'hb_r99_mythic.gdt',
                       'hb_warrior_tiers.gdt', 'hb_gold_sword.gdt', 'hb_gold_sword_motion.gdt',
                       'hb_bow.gdt', 'hb_crossbow.gdt', 'hb_fire_bow.gdt', 'hb_fire_bow_materials.gdt'];
function hbPreflight() {
  const missing = HB_TOOLS_GDTS.filter(f => !fs.existsSync(T9(f)));
  if (missing.length)
    throw new Error('Hellbound donor GDTs missing from the Mod Tools root source_data '
      + '(restore the donor library into the private TOD2Cybercity tools root): ' + missing.join(', '));
  // docs/157: the Breacher's private quality models/materials (skinOverride
  // over the ZeRoY Apex meshes). Missing = every Breacher gun links a model
  // that does not exist.
  if (!fs.existsSync(path.join(REPO, 'source_data', 'tod_breacher_apex.gdt')))
    throw new Error('source_data/tod_breacher_apex.gdt missing - run python tools/install_breacher_apex.py');
  // The Warrior (2026-09-26): the punch GDT is generated; the gauntlet donor
  // must be installed at the root (assets) AND snapshotted (the source read here).
  if (!fs.existsSync(path.join(REPO, 'source_data', 'tod_warrior_punch.gdt')))
    throw new Error('source_data/tod_warrior_punch.gdt missing - run python tools/warrior/install_punch.py');
  const t7missing = T7_TOOLS_GDTS.filter(f => !fs.existsSync(T9(f)) || !fs.existsSync(T7(f)));
  if (t7missing.length)
    throw new Error('T7 pack donor GDT missing from the tools root source_data or donor_gdt/t7: ' + t7missing.join(', '));
}

// ---- THE BREACHER (TOD II, 2026-09-23, docs/157) -----------------------------
// The HEAVY class becomes the BREACHER: Mozambique -> Remington 870 MCS ->
// Peacekeeper, replacing Mk 48 -> HK21 -> Death Machine. ZeRoY's Apex port for
// the Mozambique and Peacekeeper (the pack map one shipped), Skye's BO2 870.
const ZEROY_APEX = path.join(TOOLS, 'source_data', 'zeroy', 'APEX_BO3.gdt');
//
// THE BALANCE CONTRACT IS OVERALL DPS, NOT PER-SHOT DPS (user's call,
// 2026-09-23: "Match overall DPS"). The Skirmisher swap pinned damage-per-
// second WHILE FIRING (dpsReference), which is right for SMG -> SMG. Here a
// 60 / 94 / 150-round belt becomes a 3 / 8 / 6-round shotgun, so matching the
// firing rate alone would hand the class a reload every few shots and cut its
// real output by half or more. So each gun is pinned to its RETIRED gun's
// damage over one full cycle - empty the magazine, reload from empty:
//
//     sustained = damage x pellets x clip / (clip x interval + reload)
//
// and solved for per-pellet damage at the new gun's own clip, interval and
// reload. Both forms are pinned independently (base to the retired base, PaP
// to the retired PaP), each measured AFTER the map's own PaP derivation
// (clip x1.25, rate x1.25, reload x0.75), so a PaP swap is still the same
// step it was. Consequence the user accepted: shotguns hit much harder per
// trigger pull than the LMGs they replace, then pay it back in reloads.
//
// `interval` = fireTime + rechamberTime when the gun is boltAction (the 870
// and the Peacekeeper pump between shots; the Mozambique does not). The
// generator never scaled rechamberTime on PaP, so a pump gun's "+25% rate"
// was a +5% one - the sustained pin sets the PaP rechamber to base x PAP_FAST
// so the packed form really is 25% faster. A segmented (shell-by-shell)
// reload from empty = start + shells x per-shell + end.
//
// RESERVES keep the same SECONDS OF FIRE the retired gun carried: magazines =
// round(retired mags x retired cycle / new cycle). Pellet FALLOFF stays the
// port's own - it is what makes a shotgun a shotgun.
//
// The numbers below are the retired guns' EMITTED values (the generated GDT on
// 2026-09-23, p0/_b forms), copied the way dpsReference copies them: the
// contract must not move if those guns' GDTs are ever touched again.
const BREACHER_RETIRED = {
  // Archer direct-hit reference budget uses the GDT fire/reload cycle.
  // Native draw time, projectile travel and Fire Bow splash need the user playtest.
  // Do not claim these reference numbers are measured charged-shot DPS.
  t5_enfield: { base: {"damage": 176, "fireTime": 0.08, "clip": 30, "reload": 3.0}, up: {"damage": 220, "fireTime": 0.064, "clip": 38, "reload": 2.25}, mags: 8 },
  t9_krig6: { base: {"damage": 361, "fireTime": 0.1, "clip": 33, "reload": 3.43}, up: {"damage": 451, "fireTime": 0.08, "clip": 41, "reload": 2.5725}, mags: 9 },
  t9_ak47: { base: {"damage": 452, "fireTime": 0.08, "clip": 36, "reload": 3.25}, up: {"damage": 565, "fireTime": 0.064, "clip": 45, "reload": 2.4375}, mags: 9 },
  t6_mk48:          { base: { damage: 275, fireTime: 0.096,  clip: 60,  reload: 6.6    }, mags: 6,
                      up:   { damage: 344, fireTime: 0.0768, clip: 75,  reload: 4.95   } },
  t5_hk21:          { base: { damage: 502, fireTime: 0.112,  clip: 94,  reload: 4.75   }, mags: 5,
                      up:   { damage: 628, fireTime: 0.0896, clip: 118, reload: 3.5625 } },
  t6_death_machine: { base: { damage: 368, fireTime: 0.05,   clip: 150, reload: 4.45   }, mags: 4,
                      up:   { damage: 460, fireTime: 0.04,   clip: 188, reload: 3.3375 } },
};
const retiredCycle = r => r.clip * r.fireTime + r.reload;
const retiredDps   = r => r.damage * r.clip / retiredCycle(r);

// ---- EVEN TIERS (user 2026-09-25) ------------------------------------------
// "Can we balance the guns that are in the map currently" -> asked: the three GUN
// classes EVEN within 10% at each tier, and the Warrior keeping "the same
// difference that map 1 slasher had against the other classes". Map 1's Slasher
// blades ARE this map's Warrior blades (MELEE_TIER_DMG and swing times identical),
// so pinning every gun primary to MAP 1's GUN-CLASS MEAN per tier keeps that lead
// exactly without touching a blade. Means = map 1 (tower_of_doom_cybercity) level-0
// twins, sustained DPS (a full magazine + a reload from empty), 2026-09-25:
//   tier 1  MSMC 1341 / Enfield 1028 / Mk 48 1335         -> 1235   PaP 2401/1875/2409 -> 2228
//   tier 2  MP5 1631  / Krig 6 1858  / HK21 3089          -> 2193   PaP 3011/3321/5242 -> 3858
//   tier 3  MP7 3315  / AK-47 2790   / Death Machine 4619 -> 3574   PaP 5894/5027/7965 -> 6295
// Every skirmisher / assault (Archer) / heavy (Breacher) PRIMARY takes these through
// the sustained pin below; the retired-gun rows above now set only RESERVES.
const EVEN_CLASSES = ['assault', 'heavy'];   // the necromancer's skull is script damage (fixedCap)
const TIER_SUSTAINED = {
  1: { base: 1235, up: 2228 },
  2: { base: 2193, up: 3858 },
  3: { base: 3574, up: 6295 },
};
// One full cycle of a TUNED block: interval, clip, pellets, reload from empty.
function gunCycle(block) {
  const ft = readNum(block, 'fireTime');
  let interval = ft + (readNum(block, 'boltAction') === 1 ? (readNum(block, 'rechamberTime') || 0) : 0);
  // A Charge Shot weapon (the bows) cannot fire faster than its minimum draw
  // (2026-09-25): leaving it out overstated bow DPS by 25-40%.
  if ((readNum(block, 'chargeShotMaxLevel') || 0) > 0) interval += readNum(block, 'chargeShotMinTime') || 0;
  const clip = readNum(block, 'clipSize');
  let reload;
  if (readNum(block, 'segmentedReload') === 1) {
    const perShell = readNum(block, 'reloadAmmoAdd') || 1;
    const shells = Math.ceil((clip - (readNum(block, 'reloadStartAdd') || 0)) / perShell);
    reload = (readNum(block, 'reloadStartTime') || 0) + shells * readNum(block, 'reloadTime')
           + (readNum(block, 'reloadEndTime') || 0);
  } else {
    reload = readNum(block, 'reloadEmptyTime') || readNum(block, 'reloadTime');
  }
  return { interval, clip, reload, shot: readNum(block, 'shotCount') || 1, cycle: clip * interval + reload };
}

// ---- THE MAGE GATE (docs/114) ----------------------------------------------
// ONE flag, READ FROM THE GSC HEADER rather than duplicated here. At 0 the three
// staff rows below are enabled:false, so they are filtered out of allGuns,
// short-circuit in computeTierOverrides BEFORE its only readFileSync, and emit
// no GDT block, no zone line, no CSV row and ZERO registrations.
// source_data/tod_staff.gdt does not have to exist yet.
//
// AT 1 THIS THROWS UNTIL THE LEDGER IS PAID, and that is the guard working:
// 201 generated + 28 fixed = 229 against LEDGER_GUARD 229. Three tiers with
// `axes: []` cost 2 each = 6, the run lands at 235, and the throw sits above
// every writeFileSync. docs/114 has the payment options.
//
// existsSync-guarded so a checkout without the header degrades to OFF rather
// than taking the generator down.
const MAGE_GSH = path.join(REPO, 'scripts', 'zm', 'zm_tod2_cybercity', '_tod_mage.gsh');
const MAGE_ON = fs.existsSync(MAGE_GSH) &&
  /^\s*#define\s+TOD_MAGE_ENABLED\s+1\b/m.test(fs.readFileSync(MAGE_GSH, 'utf8'));

// ---------------------------------------------------------------------------
// PaP OPTIC REMOVAL (v18.94, 2026-09-13) - user: "remove the red dot sight from
// the RPD and the MP7 and MP5. Pap version has the sight."
//
// READ THIS BEFORE TOUCHING AN _up FORM'S SIGHT. On every Skye port in this map
// the BASE gun ships iron sights and no optic at all; the PaP half is the one
// that bolts a reflex onto tag_reflex / tag_aimpoint. So "remove the red dot"
// is a change to the _up form ONLY, and the base guns were never involved.
//
// AND IT IS TWO EDITS, NOT ONE. Deleting the attachment alone is the trap: the
// _up form ALSO swaps in the port's optic-specific ADS animations
// (am_*_snappoint_ads_up, am_*_reflex_ads_up, am_*_quickdot_ads_up), which
// raise the gun to the OPTIC's eye height rather than the iron sights'. Clear
// the model and keep those anims and the player aims down an empty rail with
// the irons sitting below the eye line - a worse gun than either state, and it
// would have looked correct in every screenshot of the hip pose. So the ads
// anims go back to the port's own non-optic pair, which the BASE form of the
// same gun already uses and already packs: PaP then aims exactly like base.
//
// The ONLY things that change are the optic and the ADS pose. Extended mag,
// heavy barrel/stock, PaP camo, damage, reload anims and the upgraded muzzle
// flash all stay - they live in other slots and other fields. Ledger-neutral:
// no weapon asset is added or removed, so the 223-registration guard does not
// move; the reflex xmodels simply stop being referenced by these three guns
// (vm_t9_reflex_quickdot_* still ships for the MAC-10 and the Stoner 63, which
// were deliberately NOT included - the user named three guns, and the Stoner is
// the other LMG whose PaP carries a dot).
//
// noOptic() writes through form.str, so it lands AFTER every ladder scale and
// cannot be undone by one. Empty string is a real clear here - strSet's value
// group is [^"]* and the altWeapon:'' precedent above proves it round-trips.
const noOptic = (adsUp, adsDown, extra) => Object.assign({
  // slot 1 = the hip optic, slot 2 = the ADS optic (ports that split them).
  // Tags and offsets go too: a stale tag_reflex with no model is harmless, but
  // leaving the MP7's Z-offset behind would strand a 2.5-unit lift in the file
  // for the next reader to wonder about.
  attachViewModel1: '',  attachViewModelTag1: '',
  attachViewModel2: '',  attachViewModelTag2: '',
  attachWorldModel1: '', attachWorldModelTag1: '',
  attachViewModelOffsetX1: '0',  attachViewModelOffsetY1: '0',  attachViewModelOffsetZ1: '0',
  attachWorldModelOffsetX1: '0', attachWorldModelOffsetY1: '0', attachWorldModelOffsetZ1: '0',
  // the half that makes it a sight removal rather than a sight deletion
  adsUpAnim: adsUp, adsDownAnim: adsDown,
}, extra || {});

const LADDER = {
  // =====================================================================
  // THE NECROMANCER (2026-09-26, user: "remove the skirmisher and add in a
  // necromancer ... the skull ... sucks in the zombies' soul and kills them").
  // The class key "skirmisher" is RETIRED; the Saug / M1927 / C.A.R. ladder
  // went with it (the Hellbound source snapshots stay in donor_gdt/ unused).
  // TIER 1 IS THE SKULL OF NAN SAPWE and it is the ONLY registered tier until
  // tiers 2/3 are designed - _tod_upgrades never deals a TIER card for a class
  // with no next gun, so this is a closed ladder, not a broken one.
  //
  // The skull does ALL of its damage in script (_tod_necro_skull.gsc), so it
  // has no DPS to normalize: `fixedCap` skips the measure-and-normalize T1
  // path and pins the class's SIDEARM CEILING to the retired Saug's recorded
  // basis (dpsReference.rawDamage 140 x CLASS_SEC_CAP_MULT 1.45475 = 204 /
  // 0.080 s = 2550 DPS), so the Bulldog / SG12 / SPAS-12 below come back
  // byte-identical. The source blocks are GENERATED by
  // tools/necromancer/make_skull_gdt.py from the stock skull_gun_zm.
  // =====================================================================
  necromancer: [
    {
      tier: 1, stem: 'tod_necro_skull', enabled: true, fixedCap: true,
      src: path.join(REPO, 'source_data', 'tod_necro_skull.gdt'), gdf: 'projectileweapon.gdf', encoding: 'latin1',
      forms: [{ srcAsset: 'tod_necro_skull',    name: s => 'tod_necro_skull' + s,    up: false },
              { srcAsset: 'tod_necro_skull_up', name: s => 'tod_necro_skull_up' + s, up: true }],
      axes: [],
      capReference: { damage: 204, fireTime: 0.080, shot: 1 },
      // the clip IS the soul meter (100), on both forms: the generic PaP clip x1.25 would make it 125
      tune: { str: { altWeapon: '' }, set: { clipSize: 100, maxAmmo: 0, startAmmo: 100 }, setUp: { clipSize: 100, maxAmmo: 0, startAmmo: 100 } },
      csv: { cost: 1300, vo: 'wpck_ray', cls: 'special' },
    },
    {
      // THE BULLDOG — the skirmisher's SECONDARY, not a ladder rung (hence
      // `secondary: true`, which skips it in computeTierOverrides so it can
      // neither become the T1 the SMGs normalize from nor be normalized itself).
      //
      // WHY IT IS GENERATED AT ALL (user 2026-08-23: "Why cant we increase
      // bulldog clip. Isnt this what we alwyads do? Same provess for twins?" —
      // and they were right, I was wrong to say it could not be done). The stock
      // s1_bulldog asset cannot be edited, but its GDT sits in the SAME mod-tools
      // source_data this generator already reads every Skye port from, so it
      // clones exactly like a twin. `axes: []` gives one base-tuned "_b" form,
      // the Death Machine's shape.
      //
      // CLIP DOUBLED, base AND PaP, per the ask: source is 6 / 9, emitted 12 /
      // 18. maxAmmo/startAmmo are counted in MAGAZINES, so doubling the clip
      // already doubles total carried rounds (96 -> 192 at the stock 16 mags)
      // WITHOUT touching the reserve keys — which is why this deliberately takes
      // only the global x1.3 reserve and NOT the skirmisher class x1.3 on top.
      // Stacking both would have put it near 324 rounds on an emergency shotgun.
      // Say the word if you want the class multiplier on it too.
      tier: 9, stem: 's1_bulldog', enabled: true, secondary: true, secTier: 1, reserveMult: 0.5,
      src: T9('skye_s1_bulldog.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 's1_bulldog',    name: s => 's1_bulldog' + s,    up: false },
              { srcAsset: 's1_bulldog_up', name: s => 's1_bulldog_up' + s, up: true }],
      axes: [],
      // PaP DAMAGE IS PINNED TO STOCK'S 240, and that is not cosmetic. The
      // generator derives every PaP form as tuned-base x PAP_UP (1.25), which is
      // correct for a ladder gun — but the AW Bulldog's stock PaP is a 2x jump
      // (120 -> 240), so the uniform 1.25 would have emitted 150 and quietly
      // shipped a PACK-A-PUNCHED BULLDOG WEAKER THAN THE STOCK ONE, right after
      // the user asked for it to be stronger. Caught by reading the emitted GDT
      // rather than trusting the regen log.
      tune: { set: { clipSize: 12 }, setUp: { clipSize: 18, damage: 240 } },
      csv: { cost: 500, vo: 'shotgun', cls: 'shotgun' },
    },
    {
      // SG12 (BO4) — skirmisher secondary T2. Port ships damage 270 / clip 10 /
      // fireTime 0.128; damage is REPLACED by the secondary-ladder normalization
      // (see computeSecondaryOverrides), so the port number is a starting point,
      // not the shipped one.
      tier: 9, stem: 't8_sg12', enabled: true, secondary: true, secTier: 2, reserveMult: 1.2,
      src: T9('skye_t8_sg12.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 't8_sg12',    name: s => 't8_sg12' + s,    up: false },
              { srcAsset: 't8_sg12_up', name: s => 't8_sg12_up' + s, up: true }],
      axes: [],
      tune: {},
      csv: { cost: 500, vo: 'shotgun', cls: 'shotgun' },
    },
    {
      // SPAS-12 (BO2) — skirmisher secondary T3. NOTE the asset is `t6_spas12`
      // while its GDT file is `skye_t6_spas-12.gdt` (hyphen in the filename, none
      // in the asset). Getting that pair wrong is the MAC-10 trap from
      // gen_tod_sounds: the lookup silently misses instead of throwing.
      // v17.4: the ceiling above carries +10% for the whole class, but the user
      // singled this gun out for a NET -5% instead. dmgMult is applied AFTER
      // the cap (see the SLASHER_SEC_BUFF note), so the correction is the RATIO
      // between the two targets — 0.95 / 1.10 — never a second absolute value.
      // Written as the division so the relationship survives a retune of either
      // number; hard-coding 0.8636 would silently decouple them.
      tier: 9, stem: 't6_spas12', enabled: true, secondary: true, secTier: 3, reserveMult: 1.4,
      dmgMult: SKIRM_SPAS_NET / SKIRM_SEC_BUFF,
      src: T9('skye_t6_spas-12.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 't6_spas12',    name: s => 't6_spas12' + s,    up: false },
              { srcAsset: 't6_spas12_up', name: s => 't6_spas12_up' + s, up: true }],
      axes: [],
      tune: {},
      csv: { cost: 500, vo: 'shotgun', cls: 'shotgun' },
    },
  ],
  assault: [
    {
      // THE MAGNUM — the assault SECONDARY, generated for ONE reason: its
      // HIT-LOCATION TABLE was the only one in the map that was not 1x body /
      // 3x head (user 2026-08-24: "THE PACK-A-PUNCHED MAGNUM HAS A 6.0 TORSO
      // MULTIPLIER AND AN 8.0 HELMET MULTIPLIER ... Fix this to match other
      // secondary multipliers"). Measured across all 172 emitted assets the
      // roster is uniformly torso/limb 1 and head/helmet/neck 3; the Magnum
      // port shipped 4.0 torso / 2.0 limb / 5.0 head on the base form and
      // 6.0 / 4.0 / 7.0 with a stray 8.0 HELMET on the PaP form. Effect at the
      // muzzle: a PaP body shot was 750 x 6 = 4,500 against the AMP63's 135 and
      // the PaP Bulldog's 300 — the strongest weapon in the map was a sidearm.
      //
      // DAMAGE IS COMPENSATED SO THE HEADSHOT NUMBER DOES NOT MOVE. Folding the
      // old head multiplier into `damage` (250 x 5 / 3 = 417, 750 x 7 / 3 =
      // 1750) leaves head damage at 1,251 and 5,250 — where it is today — while
      // body drops 1,000 -> 417 and 4,500 -> 1,750. So the gun's CEILING is
      // untouched and only the spray-the-torso case is nerfed, which is what
      // being the one weapon with a 6x torso multiplier was buying.
      //
      // WHY GENERATED AND NOT EDITED IN PLACE: skye_t9_magnum.gdt lives in the
      // shared mod-tools source_data. Map 1 has zero references to it (checked),
      // so an install-side edit would have been safe on that axis — but it is
      // still outside the repo, where a Mod Tools verify reverts it silently.
      // Cloning is the same move the Bulldog made in v10.8 and it is repo-owned.
      //
      // papKeepSource: the PaP form keeps every stat the port shipped. This gun
      // is NOT on the ladder and was not asked to be retuned — without the flag
      // the uniform PaP rule would have re-derived its damage (750 -> 312), clip
      // (12 -> 8), reserve (23 -> 16), reload, ADS and recoil off the base form.
      // Everything the PaP form should change is pinned in setUp, and nothing
      // else moves. The loc values are repeated there for the same reason: with
      // papApply bypassed there is nothing to copy them from.
      tier: 9, stem: 't9_magnum', enabled: true, secondary: true, secTier: 1, reserveMult: 0.75, papKeepSource: true,
      src: T9('skye_t9_magnum.gdt'), gdf: 'bulletweapon.gdf', encoding: 'latin1',
      forms: [{ srcAsset: 't9_magnum',    name: s => 't9_magnum' + s,    up: false },
              { srcAsset: 't9_magnum_up', name: s => 't9_magnum_up' + s, up: true }],
      axes: [],
      tune: {
        set:   Object.assign({ damage: 417,  minDamage: 367  }, LOC_FLAT),
        setUp: Object.assign({ damage: 1750, minDamage: 1447 }, LOC_FLAT, LOC_NORM),
      },
      csv: { cost: 500, vo: 'pistol', cls: 'pistol' },
    },
    {
      // MOG 12 (BO4) — assault secondary T2. Asset `t8_mog12`, GDT file
      // `skye_t8_mog_12.gdt` — underscore in the filename, none in the asset.
      tier: 9, stem: 't8_mog12', enabled: true, secondary: true, secTier: 2, reserveMult: 1.2,
      src: T9('skye_t8_mog_12.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 't8_mog12',    name: s => 't8_mog12' + s,    up: false },
              { srcAsset: 't8_mog12_up', name: s => 't8_mog12_up' + s, up: true }],
      axes: [],
      tune: {},
      csv: { cost: 500, vo: 'shotgun', cls: 'shotgun' },
    },
    {
      // EXECUTIONER (BO2) — assault secondary T3, and the one gun on this list
      // that is NOT a clean base/_up pair. Its PaP form is DUAL WIELD: the port
      // declares `t6_executioner_rdw_up_zm` (bulletweapon, the right hand, which
      // is the one the player fires) and `t6_executioner_ldw_up_zm`
      // (dualwieldweapon, the left). Only the RIGHT half is twinned here — the
      // left half is referenced BY it and is zoned as the STOCK asset in
      // zm_tod2_cybercity.zone, exactly the shape the AMP63 already ships in.
      // That is why this gun costs 3 registrations and every other one costs 2.
      tier: 9, stem: 't6_executioner', enabled: true, secondary: true, secTier: 3, reserveMult: 1.4,
      src: T9('skye_t6_executioner.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      // BOTH PaP HALVES ARE TWINNED, and that is what keeps this gun off the
      // install-side dependency list. The engine APPENDS _zm to a DualWieldWeapon
      // reference itself, so the field must hold the RUNTIME name — the port ships
      // "t6_executioner_ldw_up_zm", which the engine turns into
      // 't6_executioner_ldw_up_zm_zm' and aborts the map load with
      // "Com_ERROR: could not find alt dualwield". That is the exact failure the
      // AMP63 hit twice on 2026-08-23, and it was fixed there by editing
      // skye_t9_amp63.gdt INSIDE THE MOD TOOLS — outside the repo, where a Mod
      // Tools "verify" silently reverts it and the map stops loading again.
      // Generating both halves lets form.str write the corrected cross-reference
      // into our own emitted blocks instead, so nothing outside this repo has to
      // stay edited. Cost is 3 registrations rather than 2.
      // BOTH PaP HALVES KEEP A TRAILING _zm ON THE ASSET NAME, and the
      // DualWieldWeapon fields must NOT have it. That asymmetry is the whole
      // contract and getting it backwards is what stopped the map loading on
      // 2026-08-24 (first build of this gun):
      //   asset / zone line      t6_executioner_rdw_up_b_zm   KEEPS _zm
      //   DualWieldWeapon field  t6_executioner_ldw_up_b      NO _zm
      //   CSV upgrade_name       t6_executioner_rdw_up_b      NO _zm
      // The engine APPENDS _zm to a DualWieldWeapon reference itself, so the
      // field holds the RUNTIME name and the asset it resolves to is that plus
      // _zm. Name the halves without _zm — which looks tidier and is what the
      // first version did — and the engine goes looking for
      // 't6_executioner_ldw_up_b_zm', finds nothing, and aborts with
      // "Com_ERROR: could not find alt dualwield". Exactly the AMP63's failure
      // on 2026-08-23, reached from the opposite direction: that gun had the
      // suffix in the FIELD, this one was missing it on the ASSET.
      // The CSV needs no special-casing — the emitter already strips a trailing
      // _zm to build the script name (see scriptName in the csvRows loop), the
      // same way it does for the blades and the Enfield's PaP.
      forms: [{ srcAsset: 't6_executioner',           name: s => 't6_executioner' + s,        up: false },
              { srcAsset: 't6_executioner_rdw_up_zm', name: s => 't6_executioner_rdw_up' + s + '_zm', up: true,
                str: s => ({ DualWieldWeapon: 't6_executioner_ldw_up' + s }) },
              { srcAsset: 't6_executioner_ldw_up_zm', name: s => 't6_executioner_ldw_up' + s + '_zm', up: true,
                gdf: 'dualwieldweapon.gdf',
                str: s => ({ DualWieldWeapon: 't6_executioner_rdw_up' + s }) }],
      axes: [],
      tune: {},
      csv: { cost: 500, vo: 'pistol', cls: 'pistol' },
    },
    {
      tier: 1, stem: 'cc_bow', enabled: true,
      src: HB('hb_bow.gdt'), gdf: 'projectileweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'hb_bow_zm', name: s => 'cc_bow' + s + '_zm', up: false },
              { srcAsset: 'hb_bow_up_zm', name: s => 'cc_bow_up' + s + '_zm', up: true }],
      // 2026-09-25 (user): the ARCHER has no RECOIL / MAG SIZE cards - one '_b' form per bow.
      axes: [],
      sustainedRef: 't5_enfield', nativeQuiver: true,
      capReference: { damage: 176, fireTime: 0.08, shot: 1 },
      // 2026-09-26 SFX/VFX pass (user: "best sound and visual effects possible"):
      // the donor block shipped the PLAIN bow with NO arrow trail, NO impact
      // effect and NO impact sound (the fire bow has all three from DLC1); the
      // stock DE base bow (tools-root wpn_t7_zmb_bow.gdt, elemental_bow_zm)
      // wires exactly these, and the sources sit in share/raw/fx/dlc1 + the
      // shipped elemental_bow_sounds sheet. Raise/lower/first-raise: every bow
      // block names fly_shoulder_* (DE foley in NO sheet this map ships = silent);
      // the tod_archer_bow_* rows in tod_archer.csv carry stock DE bow WAVs, and
      // zmb_bow_first_raise is the stock sheet's own first-raise.
      tune: { recoil: RECOIL_BUMP, ads: ADS_BUMP, str: { altWeapon: '',
              projTrailEffect: 'dlc1/zmb_weapon/fx_bow_default_arrow_trail_zmb.efx',
              projExplosionEffect: 'dlc1/zmb_weapon/fx_bow_default_impact_zmb.efx',
              projExplosionSound: 'exp_elemental_bow',
              raiseSound: 'tod_archer_bow_raise_npc', raiseSoundPlayer: 'tod_archer_bow_raise_plr',
              putawaySound: 'tod_archer_bow_lower_npc', putawaySoundPlayer: 'tod_archer_bow_lower_plr',
              firstRaiseSound: 'tod_archer_bow_first_raise_npc', firstRaiseSoundPlayer: 'zmb_bow_first_raise' } },
      csv: { cost: 1250, vo: 'rifle', cls: 'rifle' },
    },
    {
      tier: 2, stem: 'cc_crossbow', enabled: true,
      src: HB('hb_crossbow.gdt'), gdf: 'projectileweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'hb_crossbow', name: s => 'cc_crossbow' + s, up: false },
              { srcAsset: 'hb_crossbow_up', name: s => 'cc_crossbow_up' + s, up: true }],
      // 2026-09-25 (user): the ARCHER has no RECOIL / MAG SIZE cards - one '_b' form per bow.
      axes: [],
      sustainedRef: 't9_krig6',

      // 2026-09-26 SFX pass: the crossbow's own raise/lower rows (hb_cb_*) are
      // real; only its first raise named the unshipped fly_shoulder_first_raise.
      tune: { recoil: RECOIL_BUMP, ads: ADS_BUMP, str: { altWeapon: '',
              firstRaiseSound: 'tod_archer_bow_first_raise_npc', firstRaiseSoundPlayer: 'zmb_bow_first_raise' } },
      csv: { cost: 1500, vo: 'rifle', cls: 'rifle' },
    },
    {
      tier: 3, stem: 'cc_fire_bow', enabled: true,
      src: HB('hb_fire_bow.gdt'), gdf: 'projectileweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'hb_fire_bow_zm', name: s => 'cc_fire_bow' + s + '_zm', up: false },
              { srcAsset: 'hb_fire_bow_up_zm', name: s => 'cc_fire_bow_up' + s + '_zm', up: true }],
      // 2026-09-25 (user): the ARCHER has no RECOIL / MAG SIZE cards - one '_b' form per bow.
      axes: [],
      sustainedRef: 't9_ak47', nativeQuiver: true,

      // 2026-09-26 SFX pass: trail/impact/impact-sound are the donor's (DLC1 rune);
      // raise/lower/first-raise named the unshipped fly_shoulder_* (see cc_bow).
      tune: { recoil: RECOIL_BUMP, ads: ADS_BUMP, str: { altWeapon: '',
              raiseSound: 'tod_archer_bow_raise_npc', raiseSoundPlayer: 'tod_archer_bow_raise_plr',
              putawaySound: 'tod_archer_bow_lower_npc', putawaySoundPlayer: 'tod_archer_bow_lower_plr',
              firstRaiseSound: 'tod_archer_bow_first_raise_npc', firstRaiseSoundPlayer: 'zmb_bow_first_raise' } },
      csv: { cost: 1500, vo: 'rifle', cls: 'rifle' },
    },
  ],
  heavy: [
    {
      // RPG (BO2) — heavy secondary T2, and the only PROJECTILE weapon on the
      // secondary ladder. Read this before retuning it.
      //
      // THE DIRECT HIT IS NORMALIZED, THE SPLASH IS NOT. `damage` (port 7000)
      // goes through computeSecondaryOverrides like every other T2, so the rocket
      // cannot out-DPS the primary it is supposed to sit under. Its
      // explosionInnerDamage/OuterDamage take only the flat -25% secondary nerf
      // and keep their shape, so the gun still kills a crowd with the blast —
      // which is the whole reason to carry a launcher. DPS is capped; the
      // FANTASY is not. If you want the port's full 7000 direct hit back, this
      // is the gun to give a `secNoNormalize: true` and a case in
      // computeSecondaryOverrides; it is deliberately not wired up, because one
      // exempt gun quietly becomes three.
      // 
      // AMMO IS THE REAL LIMITER and it is untouched: clipSize 1, 20 rockets
      // total. explosionRadius 250 is also untouched — the user was shown the
      // self-damage risk on a narrow spiral staircase and said to proceed
      // (2026-08-24), so this is a known, accepted sharp edge, not an oversight.
      // DAMAGE x2 (user 2026-08-28: "The RPG needs a 100% damage buff. Base and
      // pap."). Applied AFTER the SEC_CAP_REL ceiling in computeSecondaryOverrides
      // — the cap is what was holding this gun at 563 against a port that ships
      // 7000, and a buff placed before it would have been clamped straight back
      // to 563 and read as "the knob did nothing".
      // BOTH HALVES MOVE: direct `damage` 563 -> 1126 base / 704 -> 1408 PaP, AND
      // the two explosion-damage keys x2, because on a launcher the splash is
      // what actually kills and the direct hit is the number almost nobody lands
      // (the reasoning already written at EXPLOSION_KEYS). explosionRadius is NOT
      // in that key set, so the blast hits twice as hard over the SAME 250 units.
      // SELF-DAMAGE SCALES WITH IT — the 2026-08-24 note below records that the
      // user was shown the self-damage risk on a narrow spiral staircase and said
      // to proceed; that risk is now doubled at the same radius.
      tier: 9, stem: 't6_rpg', enabled: true, secondary: true, secTier: 2, reserveMult: 1.2, dmgMult: 2.0,
      src: T9('skye_t6_rpg.gdt'), gdf: 'projectileweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 't6_rpg',    name: s => 't6_rpg' + s,    up: false },
              { srcAsset: 't6_rpg_up', name: s => 't6_rpg_up' + s, up: true }],
      axes: [],
      tune: {},
      csv: { cost: 500, vo: 'lmg', cls: 'lmg' },
    },
    {
      // NAIL GUN (BOCW) — heavy secondary T3. Typed `projectileweapon` but every
      // explosion value is 0, so it is a bullet gun that fires nails and it
      // normalizes like any other. damage 250 / clip 40 / fireTime 0.157.
      // ITS WAV DIRECTORY IS `t9_nailgun`, NOT `t9_nail_gun` — see GDT_OF in
      // tools/gen_tod_sounds.js. Same class of trap as the MAC-10's hyphen.
      // NERFED 2026-09-09 — see the NAIL_* block near KRIG_FIRE_SCALE for why
      // dmgMult is 0.765 and not 0.85. Base and PaP both move; the PaP form
      // derives from the tuned base.
      tier: 9, stem: 't9_nail_gun', enabled: true, secondary: true, secTier: 3, reserveMult: 1.4,
      dmgMult: NAIL_DMG_MULT, clipMult: NAIL_CLIP_NERF,
      src: T9('skye_t9_nail_gun.gdt'), gdf: 'projectileweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 't9_nail_gun',    name: s => 't9_nail_gun' + s,    up: false },
              { srcAsset: 't9_nail_gun_up', name: s => 't9_nail_gun_up' + s, up: true,
                // EXPLOSION OFF (user 2026-09-01: "take away the explosion fx on the
                // pap nail gun"). The port dresses the PaP form as a launcher —
                // impactType grenade_explode, a rocket-burst efx, the grenade boom and
                // a 0.5 camera shake — over ZERO explosion damage, so it was pure
                // presentation. Blanked back to the base form's bolt impact; damage,
                // clip and the pap shot sound are untouched. Per-form by construction
                // (form.str), since the base form never had any of it.
                str: s => ({ impactType: 'bolt', projExplosionEffect: '', projExplosionSound: '',
                             projExplosionSoundPlayer: '', explosionCameraShakeDuration: '0',
                             explosionCameraShakeRadius: '0', explosionCameraShakeScale: '0' }) }],
      axes: [],
      tune: { fire: NAIL_RATE_NERF },
      csv: { cost: 500, vo: 'lmg', cls: 'lmg' },
    },
    // =====================================================================
    // TOWER OF DOOM II (2026-09-23, docs/157): the HEAVY becomes the BREACHER.
    // User: the Peacekeeper "should be taking the Blundergat's position as the
    // tier three breacher and the Mozambique should be the first tier ... the
    // single wielded Mozambique base and pack-a-punch version". Hellbound's
    // Breacher is Olympia -> Remington 870 MCS -> Blundergat; T2 stays its 870.
    // Retired: Mk 48 -> HK21 -> Death Machine (their emitted numbers are the
    // contract, BREACHER_RETIRED above - OVERALL DPS, the user's call).
    //
    // Axes and uniques do not move, so the ledger does not: p (PENETRATION) on
    // T1 and T3 (3 forms x 2 each), T2 axis-less; OVERDRIVE stays the T3's and
    // SUPPRESSING FIRE the T2's (_tod_upgrades set_guns). The user kept
    // OVERDRIVE's rules as they are (10 rounds per stack) on a 6-round gun.
    //
    // MODELS are the PRIVATE quality copies from tools/install_breacher_apex.py
    // (tod_bra_*): the same ZeRoY meshes, re-materialled on Hellbound's accepted
    // R-99 recipe. The Peacekeeper's PaP is Hellbound's mythic weapon block
    // itself (form.src), already on that recipe.
    // STEMS ARE cc_* for the docs/153 reason: Hellbound's hb_pellets.gdt emits
    // t6_rem870mcs_p0.. into the same asset namespace.
    // =====================================================================
    {
      tier: 1, stem: 'cc_mozambique', enabled: true,   // TOD II (2026-09-23): Apex Mozambique, single-wield
      src: ZEROY_APEX, gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'apex_mozambique_zm', name: s => 'cc_mozambique' + s, up: false,
                str: () => ({ gunModel: 'tod_bra_moz_view', worldModel: 'tod_bra_moz_world' }) },
              // PaP wears the white / black / red LEGENDARY 02 skin (its own
              // weapon block, same held animations as the base).
              { srcAsset: 'apex_mozambique_legend_02_zm', name: s => 'cc_mozambique_up' + s, up: true,
                // FX pass 2026-09-26: the packed flash reads PACKED (the 870 PaP's zombie ug muzzle)
                str: () => ({ gunModel: 'tod_bra_moz_pap_view', worldModel: 'tod_bra_moz_pap_world',
                              // GDT text carries doubled backslashes (as the 870 PaP's own block does)
                              viewFlashEffect: String.raw`fx\\zombie\\fx_muz_lg_shotgun_1p_ug_zmb.efx`,
                              worldFlashEffect: String.raw`fx\\zombie\\fx_muz_lg_shotgun_3p_ug_zmb.efx` }) }],
      axes: ['e'],   // 2026-09-26: PENETRATION axis retired (pinned at the old p0 'small'); 'e' = the PELLETS card
      pellets: [0, 1, 2, 3],   // 3 -> 4 / 5 / 6 (a 3-pellet gun cannot step by 20%)
      sustainedRef: 't6_mk48',
      // the Mk 48's recorded T1 reference: keeps the heavy sidearm ceiling put
      capReference: { damage: 215, fireTime: 0.075, shot: 1 },
      tune: { recoil: RECOIL_BUMP, ads: ADS_BUMP, name: 'Mozambique', nameUp: 'Mozambique Here', str: { penetrateType: 'small' } },
      csv: { cost: 1500, vo: 'shotgun', cls: 'shotgun' },
    },
    {
      tier: 2, stem: 'cc_rem870', enabled: true,       // TOD II (2026-09-23): Skye BO2 870 (Hellbound breacher T2)
      src: T9('skye_t6_remington_870_mcs.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 't6_rem870mcs',    name: s => 'cc_rem870' + s,    up: false },
              // PaP loses the port's vm_t6_reflex (no dots on packed forms, user
              // 2026-09-15) and aims down the base irons.
              { srcAsset: 't6_rem870mcs_up', name: s => 'cc_rem870_up' + s, up: true,
                str: () => noOptic('am_t6_remington870mcs_ads_up', 'am_t6_remington870mcs_ads_down') }],
      axes: ['e'],   // PELLETS card (2026-09-26)
      pellets: [0, 2, 3, 5],   // 8 -> 10 / 11 / 13 (PaP 12 -> 14 / 15 / 17), ~+20%/Lv
      sustainedRef: 't5_hk21',
      // PENETRATION medium, as the HK21 carried: the rule that a promotion is
      // never a two-step penetration downgrade (p0 on the T3 is small).
      // FX pass 2026-09-26: shotgun impact tables like the Mozambique / Peacekeeper (the BO2 port shipped bullet_small)
      tune: { recoil: RECOIL_BUMP, ads: ADS_BUMP, str: { penetrateType: 'medium',
              normalImpactsFxTable: 'shotgun_enter', normalImpactsSoundsTable: 'shotgun_impact',
              exitImpactsFxTable: 'shotgun_exit', exitImpactsSoundsTable: 'shotgun_exit', sharedWeaponSounds: 'shotgun' } },
      csv: { cost: 2750, vo: 'shotgun', cls: 'shotgun' },
    },
    {
      tier: 3, stem: 'cc_peacekeeper', enabled: true,  // TOD II (2026-09-23): Apex Peacekeeper
      src: ZEROY_APEX, gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'apex_peacekeeper_zm', name: s => 'cc_peacekeeper' + s, up: false,
                // Energy look (user 2026-09-26: "it kind of looks flat ... an energy gun"):
                // the Tac-19's blue plasma tracer from map one (skye_s1_wepcommon.gdt). The
                // PaP form below gets the same tracer.
                str: () => ({ gunModel: 'tod_bra_pk_view', worldModel: 'tod_bra_pk_world',
                              tracerType: 'mtl_s1_blue_plasma_tracer', enemyTracerType: 'mtl_s1_blue_plasma_tracer' }) },
              // PaP = Hellbound's mythic "Breach SWAT" Peacekeeper: its own
              // model, special reloads, energy tracer and firing mix.
              { srcAsset: 'hb_am_peacekeeper', name: s => 'cc_peacekeeper_up' + s, up: true,
                src: HB('hb_apex_mythic_weapons.gdt'),
                // 2026-09-26 (user: map one's Peacekeeper "shots and sounds were perfect"): map one's
                // PaP fired the plain Apex aliases; the mythic block fired hb_am peacekeeper_start.wav
                // (and its last shot was already the Apex one). Same blue plasma tracer as the base.
                str: () => ({ fireSound: 'wpn_apex_peacekeeper_fire_npc', lastShotSound: 'wpn_apex_peacekeeper_fire_npc',
                              fireSoundPlayer: 'wpn_apex_peacekeeper_fire_plr', lastShotSoundPlayer: 'wpn_apex_peacekeeper_fire_plr',
                              tracerType: 'mtl_s1_blue_plasma_tracer', enemyTracerType: 'mtl_s1_blue_plasma_tracer' }) }],
      axes: ['e'],   // 2026-09-26: PENETRATION axis retired (pinned at the old p0 'small'); 'e' = the PELLETS card
      pellets: [0, 2, 4, 7],   // 11 -> 13 / 15 / 18, ~+20%/Lv
      sustainedRef: 't6_death_machine',
      tune: { recoil: RECOIL_BUMP, ads: ADS_BUMP, name: 'Peacekeeper', nameUp: 'Peacemaker', str: { penetrateType: 'small',
              normalImpactsFxTable: 'bullet_small_energy_enter' } },   // the Havoc's energy hit sparks (map one), both forms
      csv: { cost: 5000, vo: 'shotgun', cls: 'shotgun' },
    },
  ],
  // ---- MAGE (docs/114) -- PRESENT, WIRED, AND DELIBERATELY OFF -------------
  // *** NEVER SET melee: true ON A DISABLED RUNG. *** computeTierOverrides runs
  // its melee branch BEFORE the !gun.enabled early-out and that branch does an
  // fs.readFileSync on gun.src. The staff is a projectileweapon, so this trap
  // is sidestepped by shape, not by luck.
  //
  // NO AXES, ON PURPOSE. The mage's progression is ELEMENTS, and elements are
  // SCRIPT DOMAINS: zero registrations, the map's standing no-twin law.
  // `axes: []` means variantsOf returns the single "_b" form, which is what
  // makes the class cost 6 and not 60.
  //
  // IT MUST NORMALIZE LIKE A BULLET GUN, on the CW Nail Gun's precedent
  // ("typed projectileweapon but every explosion value is 0"). The source
  // blocks MUST carry explosionInnerDamage / explosionOuterDamage 0 and put all
  // of the bolt's damage in `damage`: EXPLOSION_KEYS is deliberately outside
  // DAMAGE_KEYS and outside every papFactor set, so damage parked in splash is
  // damage the T2/T3 promotions never move and Pack-a-Punch never improves --
  // a tier ladder that means nothing.
  //
  // NO CLASS_DAMAGE_MULT / CLASS_RESERVE_MULT ROW IS NEEDED: both are read as
  // `[gun.cls] || 1`, so an absent "mage" key is a clean x1.
  // computeSecondaryOverrides `continue`s for a class with no enabled
  // secondaries, so PRIMARY_T1['mage'] never being set is harmless.
  //
  // THE srcAssets AND THE GDT PATH ARE A FORWARD DECLARATION. They are only
  // ever read when MAGE_ON is true. If the asset lane names the tiers
  // differently, the stems in _tod_classes.gsc's register_gun rows move in
  // lockstep -- there is no lint that can see a mismatch here.
  // ===================================================================
  // MVP, 2026-09-07 (user: "let's add the basic versions ... let's not let
  // it [PaP] ... let's just try to get MVP out so I can pick the class and
  // start testing it out").
  //
  // BASE FORMS ONLY -- no `up: true` rung on any tier. That is 3
  // registrations instead of 6, and it is what lets the class exist at all
  // against a ledger that was sitting at 229/229 with ZERO headroom.
  //
  // THE TIER LADDER STILL WORKS WITHOUT A PACKED STAFF, and this is not
  // luck -- both halves were checked in the tree before the forms were cut:
  //   * _tod_upgrades::tier_not_ready_reason accepts `player.tod_pap_owned`
  //     as an ALTERNATIVE to holding a name containing the up_suffix, and
  //     zm_cwpap.gsc sets exactly that latch when a class primary is bought
  //     at the machine for 5000.
  //   * reconcile_twin then asks for `tod_staff_tN_up`, finds it unlinked,
  //     and RETURNS on its own "never take the player's gun" branch.
  // So a mage pays the 5000, latches the promotion, and keeps the staff.
  // The only thing missing is a visual change on packing -- there is no
  // _up mesh to change to.
  //
  // WHEN THE LEDGER HAS ROOM, restore `{ srcAsset: <stem>_up, name: s =>
  // <stem>_up + s, up: true }` to each tier and add the three _up weapon
  // defs to source_data/tod_staff.gdt. Nothing else changes: the PaP gate
  // turns itself back on the moment the packed form links.
  // ===================================================================
  mage: [
    // v18.30 THE REVAMP: the three rungs are THREE STAFFS HELD TOGETHER
    // (lightning -> +fire -> +ice), so `flat: true` on tiers 2 and 3 -- NO
    // TIER_DPS normalization. A tier-3 mage holds all three, and its lightning
    // staff must hit as hard as its ice staff; the class TIER scales every
    // staff in script instead (_tod_mage_elements TOD_MAGE_TIER2/3_MULT, the
    // SAME 1 / 1.5625 / 2.4414 ladder -- LOCKSTEP PAIR with TIER_DPS).
    { tier: 1, stem: 'tod_staff_lightning', enabled: MAGE_ON,
      src: path.join(REPO, 'source_data', 'tod_staff.gdt'), gdf: 'projectileweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'tod_staff_lightning', name: s => 'tod_staff_lightning' + s, up: false }],
      axes: ['q'], tune: {},
      csv: { cost: 3000, vo: 'wpck_ray', cls: 'special' } },
    { tier: 2, stem: 'tod_staff_fire', enabled: MAGE_ON, flat: true,
      src: path.join(REPO, 'source_data', 'tod_staff.gdt'), gdf: 'projectileweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'tod_staff_fire',      name: s => 'tod_staff_fire' + s,      up: false }],
      axes: ['q'], tune: {},
      csv: { cost: 3000, vo: 'wpck_ray', cls: 'special' } },
    // T3's UPGRADED TIP HAS NO VIEWMODEL YET. The staged export holds
    // tod_staff_view/_world, _tip_fire_view/_world and _crystal_fire_view/_world;
    // there is no _upg view mesh (the _upg tips exist only as _world). Until one
    // is extracted this rung wears T2's tip and is visually identical to it --
    // acceptable only because the class is off.
    { tier: 3, stem: 'tod_staff_ice', enabled: MAGE_ON, flat: true,
      src: path.join(REPO, 'source_data', 'tod_staff.gdt'), gdf: 'projectileweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'tod_staff_ice',       name: s => 'tod_staff_ice' + s,       up: false }],
      axes: ['q'], tune: {},
      csv: { cost: 3000, vo: 'wpck_ray', cls: 'special' } },
  ],
  slasher: [
    {
      // UDM (Infinite Warfare) — slasher secondary T2.
      //
      // REPLACED THE VG KLAUSER (user 2026-08-25: "Replace the klauser with the
      // IW UDM"). The Klauser was the map's only gun with BROKEN ART: its port
      // declares mtl_malpha96_trigger_00 and mtl_optic_nydar_00 against
      // roughness images (i_malpha96_trigger_00_r, i_optic_nydar_00_r) that ship
      // nowhere in the tools tree, plus mtl_grip_fabric_00 and
      // mtl_pi_gen_optic_attach_00 which are declared in no GDT at all. Four
      // unresolvable material slots = white patches on a published usermap, and
      // they were the ONLY 6 unexpected linker errors this map had.
      //
      // The UDM is a clean port by comparison: a plain base/_up bulletweapon
      // pair, blank altWeapon, shotCount 1, and — unlike six of the eight
      // secondaries — it ships its OWN first_raise wav, so it needs no borrowed
      // draw sound. Ledger-neutral: 2 registrations in, 2 out.
      // CREDIT the port author (Skye_IW_UDM README: "add the people on my modme
      // post") before publish; see CREDITS.md.
      tier: 9, stem: 'iw7_udm', enabled: true, secondary: true, secTier: 2, reserveMult: 1.2 * SLASHER_SEC_BUFF, dmgMult: SLASHER_SEC_BUFF, clipMult: SLASHER_SEC_BUFF,   // v16.12 +25% x5
      // VENDORED (v16.12): the port GDT lives in the REPO now, same filename, so the
      // sync owns the root copy. Two edits ride in it: the 2026-08-28 reflex-slot
      // remaps (root-only until now, backup skye_iw7_udm.gdt.tod-reflex-orig at
      // the root) and v16.12's SIGHT REMOVAL - every reflex_* slot on all four UDM
      // meshes maps to `tod_clear` (source_data/tod_materials.gdt, a fully
      // transparent lit_transparent material over a 16x16 alpha-0 png). The grey
      // square on ADS was the sight: the port's reflex_stencil_outline slot landed
      // on a reticle_dynamic material with NO colorMap, and the lens glass sat
      // under it. Map 1 never referenced this port, so vendoring it is cross-map safe.
      src: path.join(REPO, 'source_data', 'skye_iw7_udm.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'iw7_udm',    name: s => 'iw7_udm' + s,    up: false },
              { srcAsset: 'iw7_udm_up', name: s => 'iw7_udm_up' + s, up: true }],
      axes: [],
      tune: { fire: 1 / SLASHER_SEC_BUFF, reload: 1 / SLASHER_SEC_BUFF },   // v16.12: +25% fire rate, -20% reload times
      csv: { cost: 500, vo: 'pistol', cls: 'pistol' },
    },
    {
      // RK7 GARRISON (BO4) — slasher secondary T3. The ASSET is `t8_rk7`; only
      // the GDT FILE carries the `_garrison`. A fast auto pistol (fireTime
      // 0.066), which is why the slasher line ends here: the class that has to
      // close distance gets the sidearm that covers the walk.
      tier: 9, stem: 't8_rk7', enabled: true, secondary: true, secTier: 3, reserveMult: 1.4 * SLASHER_SEC_BUFF, dmgMult: SLASHER_SEC_BUFF, clipMult: SLASHER_SEC_BUFF,   // v16.12 +25% x5
      src: T9('skye_t8_rk7_garrison.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 't8_rk7',    name: s => 't8_rk7' + s,    up: false },
              { srcAsset: 't8_rk7_up', name: s => 't8_rk7_up' + s, up: true }],
      axes: [],
      tune: { fire: 1 / SLASHER_SEC_BUFF, reload: 1 / SLASHER_SEC_BUFF },   // v16.12: +25% fire rate, -20% reload times (burstFireDelay is not a FIRE_KEY, same as PaP)
      csv: { cost: 500, vo: 'pistol', cls: 'pistol' },
    },
    // ---- THE WARRIOR (2026-09-26, user): fists -> gauntlet -> sword ----------
    // T1 ONE INCH PUNCH (Origins). The T7 pack ships it as an OFFHAND melee, so
    // tools/warrior/install_punch.py rebuilds it as a held primary on the twin
    // knives' block (source_data/tod_warrior_punch.gdt: tod_punch_zm /
    // tod_punch_up_zm, the punch's own clips + fist FX notes + sounds). Swing =
    // the melee clip's 0.7 s; fireTime 0.6 is the ladder's swing interval as on
    // every blade. The k ladder scales meleeTime from 0.7.
    {
      // THE LUNGE (user 2026-09-26 playtest: "it really should lunge to hit a
      // zombie"): the punch is the one blade exempt from MELEE_NO_LUNGE. Stock
      // lunge reach (the bat's meleeChargeRange 100) and the punch's own lunge
      // clip (vm_zom_1inchpunch_charge, _upgraded on the PaP form), which never
      // played while the range was 0. The crowd cone + fling are script:
      // _tod_warrior_melee.gsc.
      tier: 1, stem: 'cc_punch', enabled: true, melee: true, lunge: true,
      src: path.join(REPO, 'source_data', 'tod_warrior_punch.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'tod_punch_zm', name: s => 'cc_punch' + s + '_zm', up: false },
              { srcAsset: 'tod_punch_up_zm', name: s => 'cc_punch_up' + s + '_zm', up: true,
                str: () => ({ meleeChargeAnim: 'vm_zom_1inchpunch_melee_upgraded' }) }],
      axes: ['k'],
      // 2026-09-26 build-6 playtest: the lunge "looks up" = the charge clip is
      // Origins' charged UPPERCUT, so the lunge plays the form's own punch clip;
      // the kill "a second late" = meleeDelay 0.25 inherited from the knives,
      // now 0.1 on both forms (setUp: the PaP form is not reached by set).
      tune: { ads: ADS_BUMP, set: {"fireTime": 0.6, "meleeTime": 0.7, "meleeChargeTime": 0.23, "meleeDelay": 0.1},
              setUp: {"meleeDelay": 0.1},
              str: { altWeapon: '', meleeChargeRange: '100', meleeLungeRange: '0', meleeChargeAnim: 'vm_zom_1inchpunch_melee' } },
      csv: { cost: 3000, vo: 'wpck_bowie', cls: 'special', melee: true },
    },
    // T2 GAUNTLET OF SIEGFRIED = Gorod Krovi's Dragon Gauntlet, melee half
    // (`dragon_gauntlet_zm`, a HERO GADGET in stock). Both forms come from that
    // one block (the pack has no PaP twin); the PaP form wears the `_upg` view
    // mesh. tune.str turns the gadget into a held primary: inventory/gadget/
    // power fields off, unlimited ammo, the punch's sound table (the stock
    // `fist` table is not in any GDT here). Stock's own clip timings are kept
    // (meleeTime 0.6); fireTime 0.6 = the swing interval. The donor GDT is
    // install-side (root source_data, snapshot donor_gdt/t7/); its clips and
    // meshes live under the root's black_ops_3\dragon_gauntlet folders.
    {
      tier: 2, stem: 'cc_gauntlet', enabled: true, melee: true,
      src: T7('wpn_t7_zmb_dlc3_gauntlet_dragon.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'dragon_gauntlet_zm', name: s => 'cc_gauntlet' + s + '_zm', up: false },
              { srcAsset: 'dragon_gauntlet_zm', name: s => 'cc_gauntlet_up' + s + '_zm', up: true,
                str: () => ({ gunModel: 'wpn_t7_zmb_dlc3_gauntlet_dragon_upg_view' }) }],
      axes: ['k'],
      // tune.set reaches the BASE form only (the PaP form is derived through
      // setUp), so the gadget-off numbers are listed twice on purpose.
      // meleeJuke 0 (2026-09-26 build-6 playtest: every swing dashed): the swing is
      // a plain punch. (The AIM dash punch that replaced it is RETIRED, user
      // 2026-09-26: "a lunge punch we need to remove that".)
      // RIGHT-LEFT HOOK (user 2026-09-26): the engine alternates meleeAnim (the
      // gauntlet's own right swipe) and meleeLeftAnim, BO3's boxing-glove left
      // punch (installed by tools/warrior/install_punch.py; the mirrored swipe would
      // need a converter). meleeLeftTime = meleeTime, in MELEE_KEYS so Knife Speed
      // and the PaP trim scale both hands. hideTags adds tag_body = the whelp's
      // whole subtree: the gauntlet's own clips tuck it out of view, the boxing
      // clip never drives those bones, so it is hidden outright (never shown by
      // this weapon anyway). The left hook's lighter hit is script
      // (_tod_warrior_melee hook_mult).
      tune: { ads: ADS_BUMP, set: {"fireTime": 0.6, "meleeTime": 0.6, "meleeLeftTime": 0.6, "meleeChargeTime": 0.2, "unlimitedAmmo": 1, "clipOnly": 0, "heroVersion_2_0": 0, "clipSize": 0, "maxAmmo": 0, "startAmmo": 0, "meleeJuke": 0},
              setUp: {"unlimitedAmmo": 1, "clipOnly": 0, "heroVersion_2_0": 0, "clipSize": 0, "maxAmmo": 0, "startAmmo": 0, "meleeJuke": 0},
              str: { altWeapon: '', inventoryType: 'primary', gadget_type: 'none', activate_mode: 'hold', power_use_type: 'ammo',
                     ammoName: 'cc_gauntlet', clipName: 'cc_gauntlet', sharedWeaponSounds: 'tod_punch_sounds',
                     meleeLeftAnim: 'vm_boxing_gloves_melee_swipe_l',
                     hideTags: 'tag_dragon_world\\r\\ntag_body' + '\\r\\n'.repeat(31) },
              name: 'Gauntlet of Siegfried', nameUp: 'Gauntlet of Siegfried EX' },
      csv: { cost: 3000, vo: 'wpck_bowie', cls: 'special', melee: true },
    },
    {
      tier: 3, stem: 'cc_gold_sword', enabled: true, melee: true, fixedSwing: true,
      src: HB('hb_gold_sword.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'hb_gold_sword_zm', name: s => 'cc_gold_sword' + s + '_zm', up: false },
              { srcAsset: 'hb_gold_sword_up_zm', name: s => 'cc_gold_sword_up' + s + '_zm', up: true }],
      // axisMaxUp { k: 6 } RETIRED 2026-09-26 with the dark KNIFE SPEED rung (the lead:
      // set_no_dark("knifespeed")): nothing can deal cc_gold_sword_up_k6 any more.
      axes: ['k'],
      // HELLBOUND'S SWING (user 2026-09-26: "Hellbound's is a lot more smooth"):
      // the slash clip runs 1.033 s; the 0.6 / 0.65 cut here truncated it. Damage
      // per swing is the MELEE_TIER_DMG pin (unchanged); the clip's second blade
      // pass is a second hit (_tod_warrior_melee.gsc sword_second), so the rate on
      // a target is 2 hits / 1.033 s against the old 1 / 0.6 s. fixedSwing (build-6
      // playtest: the PaP trim + Knife Speed k5 still sped it up): every form swings
      // at 1.033; KNIFE SPEED no longer touches the sword.
      // THE CYBER SWORD (user 2026-09-26: "change the gold battle sword into a cyber
      // sword ... it's actually gonna be called the cyber sword"): the display name;
      // the stem stays cc_gold_sword (players never see it). Blender MCP art uses the original grip and animation skeleton.
      tune: { ads: ADS_BUMP, set: {"fireTime": 1.033, "meleeTime": 1.033, "meleeChargeTime": 0.2}, str: { altWeapon: '', gunModel: 'tod_cyber_sword_view', worldModel: 'tod_cyber_sword_world' },
              name: 'Cyber Sword', nameUp: 'Cyber Sword EX' },
      csv: { cost: 3000, vo: 'wpck_bowie', cls: 'special', melee: true },
    },
  ],
};

// Emission ORDER = the order the shipped v1 table used (mp5, krig, stoner,
// knife) so a no-ladder-change regen diffs clean; new guns append after.
const EMIT_ORDER = ['t9_mp5', 't9_krig6', 't6_mk48', 't9_me_baseballbat'];

// ---- machinery (ported) ----------------------------------------------------
function fmt(n, precision = 4) {
  if (Number.isInteger(n)) return String(n);
  return parseFloat(n.toFixed(precision)).toString();
}

// String-valued setter (absSet only matches numeric fields; penetrateType /
// altWeapon are strings).
function strSet(line, map) {
  const m = line.match(/^(\s*)"([A-Za-z0-9_]+)"\s+"([^"]*)"\s*$/);
  if (!m) return line;
  const [, indent, key] = m;
  if (!(key in map)) return line;
  return `${indent}"${key}" "${map[key]}"`;
}

function absSet(line, map) {
  const m = line.match(/^(\s*)"([A-Za-z0-9_]+)"\s+"(-?\d+(?:\.\d+)?)"\s*$/);
  if (!m) return line;
  const [, indent, key] = m;
  if (!(key in map)) return line;
  return `${indent}"${key}" "${fmt(map[key])}"`;
}

function scaleSets(line, sets, precision = 4) {
  const m = line.match(/^(\s*)"([A-Za-z0-9_]+)"\s+"(-?\d+(?:\.\d+)?)"\s*$/);
  if (!m) return line;
  const [, indent, key, valStr] = m;
  for (const [keys, factor] of sets) {
    if (factor !== 1 && keys.has(key)) {
      const v = parseFloat(valStr);
      if (v === 0) return line;   // 0 stays 0
      // INT_KEYS (clip/ammo/damage): the engine wants whole rounds — round, never truncate
      const scaled = INT_KEYS.has(key) ? Math.round(v * factor) : v * factor;
      return `${indent}"${key}" "${fmt(scaled, precision)}"`;
    }
  }
  return line;
}

// scaleSets' additive twin — same line contract, same first-match-wins rule,
// same 0-guard. The 0-guard is load-bearing here in a way it is not for a
// multiplier: x1.3 leaves a blade's 0 magazines at 0 all by itself, but +1 would
// hand every knife in the map a magazine of ammunition it has no weapon to fire.
// Values are whole magazines already, so the INT_KEYS rounding scaleSets needs
// has nothing to do — Math.round is kept only so a fractional source value
// (none today) could never emit a float into an INT-typed field.
function addSets(line, sets) {
  const m = line.match(/^(\s*)"([A-Za-z0-9_]+)"\s+"(-?\d+(?:\.\d+)?)"\s*$/);
  if (!m) return line;
  const [, indent, key, valStr] = m;
  for (const [keys, delta] of sets) {
    if (delta !== 0 && keys.has(key)) {
      const v = parseFloat(valStr);
      if (v === 0) return line;   // 0 stays 0 — melee forms carry no reserve
      const added = INT_KEYS.has(key) ? Math.round(v + delta) : v + delta;
      return `${indent}"${key}" "${fmt(added)}"`;
    }
  }
  return line;
}

function extractBlock(text, asset, gdf) {
  const decl = `"${asset}" ( "${gdf}" )`;
  const start = text.indexOf(decl);
  if (start === -1) throw new Error(`asset ${asset} (${gdf}) not found`);
  let i = text.indexOf('{', start);
  let depth = 0, end = -1;
  for (let j = i; j < text.length; j++) {
    const c = text[j];
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) { end = j; break; } }
  }
  if (end === -1) throw new Error('unbalanced braces');
  const lineStart = text.lastIndexOf('\n', start) + 1;
  return text.slice(lineStart, end + 1);
}

function makeVariant(block, asset, newName, gdf, scaleFn) {
  let scaled = 0;
  const out = block.split(/\r?\n/).map(line => {
    if (line.includes(`"${asset}" ( "${gdf}" )`))
      return line.replace(`"${asset}"`, `"${newName}"`);
    const r = scaleFn(line);
    if (r !== line) scaled++;
    return r;
  });
  return { text: out.join('\n'), scaled };
}

// numeric field reader on a (possibly tuned) block
// PER-FORM SOURCE FILE (TOD II Breacher, docs/157). `form.src` lets ONE gun's
// forms come from two GDTs: the Peacekeeper's base is the ZeRoY Apex port and
// its PaP is Hellbound's mythic "Breach SWAT" weapon, which lives in a
// different file. Absent = the gun's own `src`, so every other gun reads
// exactly what it read before. The TUNED BASE (computePapSet, the tier pass)
// is always forms[0] from gun.src; only the block a form is emitted FROM moves.
const FORM_TEXT = new Map();
function formText(gun, form, gunText) {
  if (!form.src) return gunText;
  if (!FORM_TEXT.has(form.src)) FORM_TEXT.set(form.src, fs.readFileSync(form.src, form.encoding || gun.encoding));
  return FORM_TEXT.get(form.src);
}

function readNum(block, key) {
  const m = block.match(new RegExp(`^\\s*"${key}"\\s+"(-?\\d+(?:\\.\\d+)?)"\\s*$`, 'm'));
  return m ? parseFloat(m[1]) : undefined;
}

// DISPLAY NAME override — the string the in-game HUD shows for the weapon.
// PER FORM, which is why it cannot ride tune.str (that map applies to base and
// PaP alike): a gun’s PaP form wants its own name. Both names come from the
// port’s source GDT unless a gun sets tune.name / tune.nameUp.
function nameSet(gun, line, isUp) {
  if (!gun.tune || !gun.tune.name) return line;
  return strSet(line, { displayName: isUp ? (gun.tune.nameUp || gun.tune.name) : gun.tune.name });
}

// ---- the base tune -----------------------------------------------------------
// Every variant of a gun passes through this BEFORE its ladder scaling. The
// base form gets the hand tune (parity pass + per-gun overrides + the tier
// overrides computed below); the PaP form gets papApply() — every tuned stat
// overwritten with the TUNED-BASE value made 25% better — then the melee tier
// damage (exempt from the uniform rule) set explicitly.
function baseTune(gun, line, isUp) {
  if (isUp) {
    // `papKeepSource` OPTS A GUN OUT OF THE UNIFORM PaP DERIVATION entirely, so
    // its _up form keeps every value the port shipped and only tune.setUp moves.
    // Needed by the Magnum: it is generated for ONE reason (its hit-location
    // table), and papApply would otherwise re-derive ~40 of its stats from the
    // base x the PaP factors — quietly rewriting its damage, clip, reserve,
    // reload, ADS and recoil on a gun nobody asked to retune.
    let l = gun.papKeepSource ? line : papApply(gun.stem, line);
    if (gun.melee && gun.override && gun.override.meleeDamageUp !== undefined)
      l = absSet(l, { meleeDamage: gun.override.meleeDamageUp,
                      meleeFromBehindDamage: gun.override.meleeBehindUp });
    // string overrides apply to EVERY form — the Enfield's PaP form is the one
    // carrying the Masterkey altWeapon (caught 2026-08-22: the first 2b build
    // left it on the _up variants = the boot-trap class, never shipped)
    // ABSOLUTE PaP-SIDE VALUES (v10.8). The PaP form is otherwise derived
    // entirely from the SOURCE _up block times PAP_UP, so there was no way to
    // pin a number on it — fine for a ladder gun, wrong for the Bulldog, whose
    // PaP clip the user specified directly ("clip size can double for base and
    // pap bulldog"). Applied AFTER papApply so it wins over the x1.25.
    if (gun.tune.setUp) l = absSet(l, gun.tune.setUp);
    // SPLASH ONLY — and the asymmetry with `damage` is the whole point.
    //
    // BUG THIS FIXES (shipped 2026-08-24, caught the same day): this used to
    // scale DAMAGE_KEYS here too, which double-applied the secondary nerf to
    // every PaP form that derives its damage through papApply. papApply reads
    // the TUNED BASE — which already carries the nerf, or an override.damage
    // that embeds it — and multiplies by PAP_UP. Scaling again here made the
    // PaP form 1.25 x 0.75 = 0.9375 of the base, i.e. EVERY Pack-a-Punched
    // secondary was WEAKER THAN ITS OWN BASE FORM: the RPG went 563 -> 528, the
    // Nail Gun 460 -> 431, the SG12 138 -> 130, the Klauser 165 -> 155.
    //
    // It was correct when it was written and the only secondaries were the
    // Bulldog and the Magnum, because BOTH pin their PaP damage as a literal
    // and so bypass papApply entirely. Adding eight secondaries that do not pin
    // turned a targeted fix into a roster-wide bug. Those two guns now get
    // their pin DERIVED from the final base damage in computeSecondaryOverrides
    // instead, so PaP = base x PAP_UP for every secondary by one rule.
    //
    // EXPLOSION KEYS STILL BELONG HERE. They are in no papFactor set, so
    // papApply never touches them and the _up form would otherwise keep the raw
    // PORT splash — the RPG's 2500/1000 rather than the nerfed 1875/750. Here
    // the scaling applies exactly once, which is what it did before and still
    // does. (Note this also means PaP grants no splash increase; that follows
    // the existing PAP_UP_KEYS design and is not changed here.)
    // (per-gun dmgMult folded into the SAME factor for the same first-match-wins
    // reason as the base branch — and it must be here too, because explosion
    // keys are in no papFactor set, so without this line the _up form keeps the
    // raw PORT splash and a buffed base would ship a WEAKER Pack-a-Punched
    // launcher than its own base form. That exact inversion is the 2026-08-24
    // bug recorded above; this is the same hazard from the other direction.)
    {
      const explUp = (gun.secondary ? SECONDARY_DMG_MULT : 1) * (gun.dmgMult || 1);
      if (explUp !== 1) l = scaleSets(l, [[EXPLOSION_KEYS, explUp]]);
    }

    // RESERVE ON A papKeepSource GUN — the Magnum, and only the Magnum today.
    //
    // papKeepSource bypasses papApply entirely, so the _up form keeps the PORT's
    // own maxAmmo instead of inheriting the tuned base's. That means a per-gun
    // reserveMult lands on the base and NOT on the PaP form: the 2026-08-25 "cut
    // the Magnum by 25%" pass moved base 96 -> 72 and left PaP sitting at 276.
    //
    // Only gun.reserveMult is applied here, deliberately — NOT the global
    // RESERVE_MULT or the class knob. Those have never reached a papKeepSource
    // _up form (which is why the Magnum's PaP reserve is 23 raw magazines against
    // a 12-magazine base), and folding them in now would be a silent balance
    // change to a gun nobody asked to retune beyond the 25%.
    if (gun.papKeepSource && gun.reserveMult && gun.reserveMult !== 1)
      l = scaleSets(l, [[RESERVE_KEYS, gun.reserveMult]]);
    // ...and the +1 MAGAZINE, for the same reason and with the opposite verdict
    // to the paragraph above. RESERVE_MULT stays out of this branch because it
    // was a map-wide economy default that had never reached a papKeepSource _up
    // form; RESERVE_ADD goes IN because the user asked for one extra magazine on
    // ALL guns by name (2026-08-26), and without this line the Magnum's PaP form
    // is the single asset in the map that does not get it. Every other _up form
    // inherits the magazine through papApply/PAP_COPY_KEYS, which this branch
    // bypasses — so this is not a second application, it is the only one.
    // gun.reserveAdd rides along for the same reason and by the same rule (one
    // summed delta — addSets is first-match-wins). No papKeepSource gun sets it
    // today; carrying it here is what stops the next one silently missing its
    // per-gun magazine on the PaP form, which is the exact bug this branch
    // exists to fix for RESERVE_ADD.
    if (gun.papKeepSource && (RESERVE_ADD + (gun.reserveAdd || 0)) !== 0)
      l = addSets(l, [[RESERVE_KEYS, RESERVE_ADD + (gun.reserveAdd || 0)]]);
    if (gun.tune.str) l = strSet(l, gun.tune.str);
    // v10.23: was `if (gun.melee)`, which left meleeChargeRange 120 on all 136
    // non-melee emitted assets — every bullet weapon still LUNGED on a gun bash,
    // despite the roster-wide "remove the lunge swing" pass. That pass only ever
    // reached the blades. meleeLungeRange is already 0 on the ports; this zeroes
    // the charge lunge too. The bash itself is unaffected — it still connects at
    // meleeRange, exactly as it does on the blades, which have run at 0 since
    // that pass shipped.
    if (!gun.lunge) l = strSet(l, MELEE_NO_LUNGE);
    l = nameSet(gun, l, true);
    return l;
  }
  const set = Object.assign({ moveSpeedScale: 1 }, LOC_NORM, gun.tune.set || {});
  if (gun.override) {
    for (const k of ['damage', 'minDamage', 'damageMin', 'clipSize'])
      if (gun.override[k] !== undefined) set[k] = gun.override[k];
    if (gun.melee && gun.override.meleeDamage !== undefined) {
      set.meleeDamage = gun.override.meleeDamage;
      set.meleeFromBehindDamage = gun.override.meleeBehind;
    }
  }
  let l = absSet(line, set);
  const sets = [];
  if (gun.tune.recoil) sets.push([RECOIL_KEYS, gun.tune.recoil]);
  if (gun.tune.ads) sets.push([ADS_KEYS, gun.tune.ads]);
  if (gun.tune.fire) sets.push([FIRE_KEYS, gun.tune.fire]);
  if (gun.tune.reload) sets.push([RELOAD_KEYS, gun.tune.reload]);   // v16.12: every reload time; the PaP form inherits it through computePapSet (PAP_TRIM on the TUNED base)
  // Global +30% reserve (v9.36) TIMES the class knob (v10.8) — skirmisher ends
  // at 1.69x its GDT reserve. gun.cls is stamped in computeTierOverrides.
  // Secondaries take the GLOBAL reserve bump only — the class knobs are a
  // decision about the SMG LINE, and the Bulldog's own clip change already
  // doubles its carried rounds (see its LADDER entry).
  // gun.reserveMult is the PER-GUN knob (the HK21's -25%), folded into the SAME
  // factor as the other two on purpose: scaleSets returns on its first matching
  // set, so a second [RESERVE_KEYS, x] push would be silently ignored.
  const crm = gun.secondary ? 1 : (CLASS_RESERVE_MULT[gun.cls] || 1);
  sets.push([RESERVE_KEYS, RESERVE_MULT * crm * (gun.reserveMult || 1)]);
  // CLASS DAMAGE — T1 ONLY. `gun.override.damage` is set for T2/T3 by
  // computeTierOverrides and absSet has already written it above, so scaling
  // here would compound on top of the value that was ALREADY derived from the
  // buffed T1. Guarding on the override is what keeps the buff exactly +10%
  // across the whole ladder instead of +10% / +21% / +21%.
  const cdm = gun.secondary ? SECONDARY_DMG_MULT : (CLASS_DAMAGE_MULT[gun.cls] || 1);
  if (cdm !== 1 && !(gun.override && gun.override.damage !== undefined))
    sets.push([DAMAGE_KEYS, cdm]);
  // Splash always takes the secondary nerf, override or not — a normalized
  // `damage` says nothing about explosionInnerDamage.
  // ...AND the per-gun dmgMult rides the SAME factor, never a second push:
  // scaleSets is first-match-wins, so a separate [EXPLOSION_KEYS, x] entry
  // would be silently dropped (the identical trap reserveAdd documents).
  // The guard is no longer secondary-only — a PRIMARY with splash and a
  // dmgMult would otherwise get its direct hit buffed and its splash left
  // behind. EXPLOSION_KEYS holds only explosionInner/OuterDamage;
  // explosionRadius is deliberately NOT in it, so this scales how hard the
  // blast hits and never how far it reaches.
  const secExpl = gun.secondary ? SECONDARY_DMG_MULT : 1;
  const explMult = secExpl * (gun.dmgMult || 1);
  if (explMult !== 1)
    sets.push([EXPLOSION_KEYS, explMult]);
  if (sets.length) l = scaleSets(l, sets);
  // +1 MAGAZINE, AFTER every reserve multiplier (RESERVE_ADD's header). Order is
  // the contract: round(src x mults) + 1, never (src + 1) x mults, or the class
  // knob would quietly turn one magazine into 1.3 of one.
  // gun.reserveAdd is the PER-GUN extra magazine (the Death Machine's +1), and
  // it is SUMMED INTO THE SAME DELTA rather than pushed as a second entry:
  // addSets is first-match-wins exactly like scaleSets, so a second
  // [RESERVE_KEYS, x] would be silently dropped. Additive, not multiplicative,
  // for the reason in RESERVE_ADD's header — reserves here run 2 to 24
  // magazines, so a factor that helps the 2 hands the 24 a fistful.
  const radd = RESERVE_ADD + (gun.reserveAdd || 0);
  if (radd !== 0) l = addSets(l, [[RESERVE_KEYS, radd]]);
  // Starter replacements retain the previous emitted reserve AFTER global/class
  // multipliers. PaP copies these tuned values through PAP_COPY_KEYS.
  if (gun.tune.reserveMags !== undefined)
    l = absSet(l, { maxAmmo: gun.tune.reserveMags, startAmmo: gun.tune.reserveMags });
  if (gun.tune.str) l = strSet(l, gun.tune.str);
  if (!gun.lunge) l = strSet(l, MELEE_NO_LUNGE); // Bat alone retains its authored lunge.
  l = nameSet(gun, l, false);
  return l;
}

// gun.fixedSwing (2026-09-26, the Warrior's Gold Battle Sword; generic - any gun
// may set it): the swing timing is the clip's own and NOTHING scales it. In this
// engine meleeTime is also the swing clip's playback length, so a shorter
// meleeTime plays the slash faster (the user: "swinging way too fast ... not
// matching Hellbound" on cc_gold_sword_up_k5). Two lanes honour it:
//   ladderScale  - an axis set on MELEE_KEYS is skipped (the k twins keep the
//                  base timing; their other keys, if any, still scale);
//   PAP_EXEMPT   - fireTime / meleeTime / meleeChargeTime are not PaP'd (the
//                  melee PAP_EXEMPT block below adds them).
// The gun still carries its axes, so the script's registered variant names all
// exist; they simply swing the same.
const FIXED_SWING_KEYS = ['fireTime', 'meleeTime', 'meleeLeftTime', 'meleeChargeTime'];

// the ladder scaling for one variant (levels = { letter: level })
function ladderScale(gun, line, levels) {
  let l = line;
  for (const letter of gun.axes) {
    const ax = AXIS[letter];
    const lv = levels[letter];
    if (gun.fixedSwing && ax.sets && ax.sets.every(([keys]) => keys === MELEE_KEYS)) continue;
    if (ax.pen) l = strSet(l, { penetrateType: PEN_TIER[lv] });
    else if (ax.pellets) {
      if (!gun.pellets || gun.pellets.length !== ax.levels + 1) throw new Error(`${gun.stem}: axis 'e' needs gun.pellets[0..${ax.levels}]`);
      l = l.replace(/^(\s*"shotCount"\s+")(\d+)(")/, (m, a, n, b) => a + (parseInt(n, 10) + gun.pellets[lv]) + b);
    }
    // Staff thirds need five decimals (0.28125 / 3 = 0.09375).
    else l = scaleSets(l, ax.sets.map(([keys, steps]) => [keys, steps[lv]]), letter === 'q' ? 5 : 4);
  }
  return l;
}

// PaP stat sets, per stem, derived from the TUNED base block.
const PAP_SETS = {};
const PAP_EXEMPT = {};   // stem -> Set(keys) the uniform rule must not touch

function papFactor(key) {
  if (PAP_UP_KEYS.has(key)) return PAP_UP;
  if (FIRE_KEYS.has(key)) return PAP_FAST;
  if (RELOAD_KEYS.has(key) || SWAP_KEYS.has(key) || ADS_KEYS.has(key)
    || RECOIL_KEYS.has(key) || MELEE_KEYS.has(key)) return PAP_TRIM;
  if (PAP_COPY_KEYS.has(key)) return 1;
  return undefined;   // not a papped stat — the _up form keeps its own value
}

function computePapSet(stem, tunedBaseBlock) {
  const set = {};
  for (const line of tunedBaseBlock.split(/\r?\n/)) {
    const m = line.match(/^\s*"([A-Za-z0-9_]+)"\s+"(-?\d+(?:\.\d+)?)"\s*$/);
    if (!m) continue;
    const [, key, valStr] = m;
    if (PAP_EXEMPT[stem] && PAP_EXEMPT[stem].has(key)) continue;
    const f = papFactor(key);
    if (f === undefined) continue;
    const v = parseFloat(valStr);
    if (v === 0) continue;                  // 0 stays 0 (scaleSets convention)
    const scaled = v * f;
    // meleeDamage joins the INT set here — map 1's INT-typed damage trap
    set[key] = (INT_KEYS.has(key) || key === 'meleeDamage') ? Math.round(scaled) : scaled;
  }
  set.moveSpeedScale = 1;   // class_speed_base owns speed on every form
  PAP_SETS[stem] = set;
}

function papApply(stem, line) {
  const set = PAP_SETS[stem];
  if (!set) throw new Error(`papApply before computePapSet for ${stem}`);
  return absSet(line, set);
}

// cartesian enumeration of a gun's variants: [{ suffix, levels }]
// PER-GUN AXIS CEILING (v17.10). `gun.axisMax = { m: 4 }` raises (or lowers)
// how many rungs THIS gun gets on that axis, instead of every gun that carries
// it. Added for the DARK UPGRADES: the user's rule is that a dark twin exists
// only on the class's TIER 3 gun, so the AK-47 needs an m4 the Enfield and Krig
// 6 must not have, the MP7 an h4 the MAC-10 and MP5 must not have, and the
// Leviathan a k6 the other two blades must not have.
//
// WITHOUT THIS THE FEATURE IS UNAFFORDABLE: raising AXIS.m.levels globally adds
// a rung to all three assault guns (+18 registrations, against a guard with 4
// free) to buy one that only the AK can ever use.
// `gun.axisMaxUp = { m: 4 }` raises that axis by the DARK rung on the PACKED
// form ONLY. Two user rules stack here (2026-09-04): a dark twin exists only on
// the class TIER 3 gun, and only on its Pack-a-Punch version.
//
// FORM-AWARE ON PURPOSE. The base form must NOT carry the rung, or half the
// saving disappears and an un-packed player could be handed a variant that
// exists but should not.
function axisLevels(gun, letter, isUp) {
  if (isUp && gun.axisMaxUp && typeof gun.axisMaxUp[letter] === 'number')
    return gun.axisMaxUp[letter];
  return AXIS[letter].levels;
}

function variantsOf(gun, isUp) {
  if (!gun.axes.length) return [{ suffix: '_b', levels: {} }];
  let combos = [{}];
  for (const letter of gun.axes) {
    const next = [];
    for (const c of combos)
      for (let lv = 0; lv <= axisLevels(gun, letter, isUp); lv++)
        next.push(Object.assign({}, c, { [letter]: lv }));
    combos = next;
  }
  return combos.map(levels => ({
    suffix: '_' + gun.axes.map(l => l + levels[l]).join(''),
    levels,
  }));
}

// ---- tier overrides ------------------------------------------------------------
// Walk each class in tier order. With the T1 gun ENABLED, every enabled higher
// tier gets damage normalized to T1's tuned DPS x TIER_DPS and a clip no
// smaller than the tier below x CLIP_STEP. Melee guns get MELEE_TIER_DMG.
function computeTierOverrides() {
  hbPreflight();
  for (const [cls, guns] of Object.entries(LADDER)) {
    // Stamp the class onto every gun BEFORE any baseTune call — the per-class
    // reserve/damage knobs read it, and computeTierOverrides calls baseTune to
    // measure the tuned T1, so the stamp has to exist by then or the T1 the
    // whole ladder is normalized from would be measured un-buffed.
    for (const g of guns) g.cls = cls;
    const sorted = guns.slice().sort((a, b) => a.tier - b.tier);
    let t1 = null;        // { damage, fireTime } of the tuned T1 base
    let prevClip = null;
    for (const gun of sorted) {
      gun.override = {};
      // SECONDARIES ARE NOT LADDER RUNGS (v10.8). The Bulldog is the
      // skirmisher's sidearm, not a tier of its ladder: it must never become
      // `t1` for normalization, never be normalized FROM t1, and never move
      // `prevClip` (the never-shrink floor belongs to the primary line only).
      // It is emitted with its own tune and nothing else.
      if (gun.secondary) continue;
      if (gun.melee) {
        gun.override.meleeDamage = MELEE_TIER_DMG[gun.tier][0];
        gun.override.meleeDamageUp = MELEE_TIER_DMG[gun.tier][1];
        gun.override.meleeBehind   = Math.round(MELEE_TIER_DMG[gun.tier][0] * BACKSTAB_MULT);
        gun.override.meleeBehindUp = Math.round(MELEE_TIER_DMG[gun.tier][1] * BACKSTAB_MULT);
        // meleeFromBehindDamage is in NO papFactor set, so the uniform PaP rule
        // never touches it and the _up form would otherwise keep the port's own
        // number — which is exactly how 20,000 and 0 survived. It is listed here
        // anyway so that adding it to PAP_UP_KEYS later cannot silently
        // double-apply on top of the explicit set below.
        PAP_EXEMPT[gun.stem] = new Set(['meleeDamage', 'meleeFromBehindDamage'].concat(gun.fixedSwing ? FIXED_SWING_KEYS : []));
        // MELEE PRIMARY T1 -> a DPS the secondary cap can be computed from.
        // The slasher's whole primary line is melee, so without this the class
        // has no PRIMARY_T1 entry at all and its sidearms would be uncapped.
        // Swing damage over swing time (fireTime IS the swing interval on these
        // blades, 0.6s on the level-0 knife).
        //
        // TREAT THE RESULT WITH SUSPICION when you are tuning by it. 2000/0.6 =
        // 3,333 "DPS" is real only in contact range, on one zombie, while you
        // are being hit. A RANGED sidearm at the same number is strictly
        // stronger in practice, which is why the user chose ceiling mode: the
        // slasher's sidearms are all comfortably under this cap today and this
        // number never actually binds. If a future slasher sidearm does hit it,
        // scale it down here rather than trusting the equivalence.
        if (gun.tier === 1) {
          const mtext = fs.readFileSync(gun.src, gun.encoding);
          const mraw = extractBlock(mtext, gun.forms[0].srcAsset, gun.forms[0].gdf || gun.gdf);
          const mSwing = readNum(mraw.split(/\r?\n/).map(l => baseTune(gun, l, false)).join('\n'), 'fireTime');
          if (mSwing) PRIMARY_T1[cls] = { dps: MELEE_TIER_DMG[1][0] / mSwing, melee: true };
        }
        continue;
      }
      if (!gun.enabled) { t1 = (gun.tier === 1) ? null : t1; continue; }
      if (gun.fixedCap) {
        // SCRIPT-DAMAGE PRIMARY (the necromancer's skull): nothing to measure.
        // Record the pinned sidearm ceiling and emit the forms as authored.
        const c = gun.capReference;
        const dps = c.damage * (c.shot || 1) / c.fireTime;
        PRIMARY_T1[cls] = { dps, capDps: dps };
        t1 = { damage: c.damage, fireTime: c.fireTime };
        console.log(`  tier ${gun.tier} ${gun.stem}: FIXED CAP (script damage) - sidearm ceiling ${Math.round(dps)} dps`);
        continue;
      }
      const text = fs.readFileSync(gun.src, gun.encoding);
      const raw = extractBlock(text, gun.forms[0].srcAsset, gun.forms[0].gdf || gun.gdf);
      // SUSTAINED PIN (the Breacher, docs/157 - see BREACHER_RETIRED). Every
      // tier is pinned to its own retired gun, so none of TIER_DPS, the
      // never-shrink clip floor or dpsReference applies to this ladder.
      const even = EVEN_CLASSES.includes(cls) && !gun.secondary && !gun.flat && TIER_SUSTAINED[gun.tier];
      if (gun.sustainedRef || even) {
        const ret = gun.sustainedRef ? BREACHER_RETIRED[gun.sustainedRef] : undefined;
        const tgtBase = even ? TIER_SUSTAINED[gun.tier].base : retiredDps(ret.base);
        const tgtUp   = even ? TIER_SUSTAINED[gun.tier].up   : retiredDps(ret.up);
        const tuneOf = (isUp, blk) => blk.split(/\r?\n/).map(l => baseTune(gun, l, isUp)).join('\n');
        // reserve first: it moves no cycle term (the Skirmisher keeps its pinned 11 mags)
        const probe = gunCycle(tuneOf(false, raw));
        if (ret && !gun.nativeQuiver) gun.tune.reserveMags = Math.max(1, Math.round(ret.mags * retiredCycle(ret.base) / probe.cycle));
        else { gun.tune.set = Object.assign({}, gun.tune.set, { maxAmmo: 0, startAmmo: readNum(raw, "clipSize") }); }
        // BASE: per-pellet damage that reproduces the retired sustained DPS
        const b = gunCycle(tuneOf(false, raw));
        const srcDmg = readNum(raw, 'damage'), srcMin = readNum(raw, 'minDamage');
        gun.override.damage = Math.round(tgtBase * b.cycle / (b.clip * b.shot));
        if (srcMin !== undefined && srcDmg) gun.override.minDamage = Math.round(gun.override.damage * srcMin / srcDmg);
        // PaP: derive exactly as the emit loop will (papApply over the up block)
        const tunedBase = tuneOf(false, raw);
        computePapSet(gun.stem, tunedBase);
        const upForm = gun.forms.find(f => f.up);
        const upRaw = extractBlock(formText(gun, upForm, text), upForm.srcAsset, upForm.gdf || gun.gdf);
        const baseRechamber = readNum(tunedBase, 'rechamberTime');
        const setUp = Object.assign({}, gun.tune.setUp);
        if (readNum(tunedBase, 'boltAction') === 1 && baseRechamber)
          setUp.rechamberTime = +(baseRechamber * PAP_FAST).toFixed(4);
        gun.tune.setUp = setUp;
        const u = gunCycle(tuneOf(true, upRaw));
        setUp.damage = Math.round(tgtUp * u.cycle / (u.clip * u.shot));
        if (srcMin !== undefined && srcDmg) setUp.minDamage = Math.round(setUp.damage * srcMin / srcDmg);
        const perPull = (d, c) => Math.round(d * c.shot * c.clip / c.cycle);
        console.log(`  tier ${gun.tier} ${gun.stem}: SUSTAINED pin to ${even ? 'EVEN tier ' + gun.tier : gun.sustainedRef} - base ${gun.override.damage} x${b.shot} `
          + `(clip ${b.clip}, ${b.interval.toFixed(3)}s, reload ${b.reload.toFixed(3)}s) = ${perPull(gun.override.damage, b)} dps vs ${Math.round(tgtBase)}; `
          + `PaP ${setUp.damage} x${u.shot} (clip ${u.clip}, ${u.interval.toFixed(3)}s, reload ${u.reload.toFixed(3)}s) = ${perPull(setUp.damage, u)} dps vs ${Math.round(tgtUp)}; `
          + `reserve ${gun.tune.reserveMags} mags`);
        if (gun.tier === 1) {
          // THE SIDEARM CEILING DOES NOT MOVE. The heavy's secondaries (RPG, Nail
          // Gun) are capped off PRIMARY_T1.capDps; the class keeps the Mk 48's
          // recorded reference so they come back byte-identical.
          // The Skirmisher's basis stays the MSMC's (dpsReference.rawDamage x
          // CLASS_SEC_CAP_MULT / fireTime = 204 / 0.080 = 2550), so the Bulldog /
          // SG12 / SPAS-12 ceiling does not move either.
          const c = gun.capReference || { damage: Math.round(gun.dpsReference.rawDamage * CLASS_SEC_CAP_MULT[cls]), fireTime: gun.dpsReference.fireTime };
          const dps = c.damage * (c.shot || 1) / c.fireTime;
          PRIMARY_T1[cls] = { dps, capDps: dps };
          t1 = { damage: c.damage, fireTime: c.fireTime };
        }
        prevClip = b.clip;
        continue;
      }
      if (gun.dpsReference) {
        const ref = gun.dpsReference;
        const ratio = readNum(raw, 'fireTime') / ref.fireTime;
        gun.override.damage = Math.round(ref.damage * ratio);
        gun.override.minDamage = Math.round(ref.minDamage * ratio);
        gun.tune.setUp = Object.assign({}, gun.tune.setUp, {
          damage: Math.round(ref.upDamage * ratio),
          minDamage: Math.round(ref.upMinDamage * ratio),
        });
      }
      // the tuned base WITHOUT tier overrides (override is still {} here)
      const tuned = raw.split(/\r?\n/).map(l => baseTune(gun, l, false)).join('\n');
      const damage = readNum(tuned, 'damage');
      const minDamage = readNum(tuned, 'minDamage');
      const fireTime = readNum(tuned, 'fireTime');
      const clip = readNum(tuned, 'clipSize');
      if (gun.tier === 1) {
        // The replacement's integer rounding and larger magazine must not
        // rebalance later tiers or their sidearm ceilings.
        t1 = gun.dpsReference || { damage, fireTime };
        // BULLET PRIMARY T1 -> the DPS the secondary cap is computed from.
        // shotCount belongs in it for the same reason it belongs in the
        // secondary math: `damage` is PER PROJECTILE. No primary is a shotgun
        // today, so every one of these is x1 — recording it anyway is what stops
        // a future shotgun primary silently capping its class's sidearms 8x too
        // low.
        // capDps — THE BASIS THE SECONDARY CEILING USES, recorded separately so
        // a primaries-only knob cannot move the sidearms (v14.32). It is derived
        // by UNDOING CLASS_DAMAGE_MULT and re-applying CLASS_SEC_CAP_MULT on the
        // damage BEFORE it was rounded to an integer. Doing it here rather than
        // scaling p.dps at the cap site matters: `damage` is already rounded, so
        // multiplying it back up by 1.3225/1.19025 overshot and moved the
        // SPAS-12 from 128 to 129 — a gun the order excluded. Absent entry =
        // capDps is dps, i.e. the default coupling, exactly as before.
        const shotC = readNum(tuned, 'shotCount') || 1;
        const dps = t1.damage * shotC / t1.fireTime;
        let capDps = dps;
        if (CLASS_SEC_CAP_MULT[cls]) {
          // Re-derive from the RAW PORT damage, applying the pinned multiplier
          // and rounding exactly as baseTune's DAMAGE_KEYS scale does. Going
          // back to `raw` is what makes this exact: `damage` above is already
          // rounded at the NEW multiplier, and un-dividing it lands between
          // integers (167/1.19025x1.3225 = 185.55 -> 186, against a true 185),
          // which moved the SPAS-12 128 -> 129. A gun the order excluded must
          // come back byte-identical, so the basis is reconstructed, not scaled.
          const rawDmg = gun.dpsReference?.rawDamage ?? readNum(raw, 'damage');
          if (rawDmg) capDps = Math.round(rawDmg * CLASS_SEC_CAP_MULT[cls]) * shotC / (gun.dpsReference?.fireTime || fireTime);
        }
        PRIMARY_T1[cls] = { dps, capDps };
        prevClip = gun.dpsReference?.clipSize || clip;
        continue;
      }
      if (!t1) {
        console.log(`  note: ${gun.stem} (tier ${gun.tier}) emitted UN-normalized — the ${cls} T1 gun is not enabled yet`);
        prevClip = clip;
        continue;
      }
      // FLAT RUNG (v18.30, the mage's staffs): held TOGETHER with T1, not
      // instead of it, so it ships the source block's own damage and clip --
      // no TIER_DPS, no never-shrink floor. The class tier scales it in script.
      if (gun.flat) {
        console.log(`  tier ${gun.tier} ${gun.stem}: FLAT (held with T1; no normalization)`);
        prevClip = clip;
        continue;
      }
      // DPS normalization at the gun's own fire time
      const dmg = Math.round(t1.damage * TIER_DPS[gun.tier] * fireTime / t1.fireTime);
      gun.override.damage = dmg;
      if (minDamage !== undefined && damage) gun.override.minDamage = Math.round(dmg * minDamage / damage);
      // never-shrink clip
      const floor = Math.round(prevClip * CLIP_STEP);
      gun.override.clipSize = Math.max(clip, floor);
      // PER-GUN CLIP NERF, applied AFTER the never-shrink floor. Order matters:
      // the floor exists to stop a promotion shrinking your magazine, but an
      // explicit nerf has to be able to win over it or it would be silently
      // clamped back up. prevClip below takes the NERFED value, so the next
      // tier's floor derives from what this gun actually ships with.
      if (gun.clipMult) gun.override.clipSize = Math.round(gun.override.clipSize * gun.clipMult);
      // PER-GUN DAMAGE BUMP, applied AFTER the DPS normalization for the same
      // reason clipMult is applied after the clip floor: normalization SETS
      // override.damage outright, so a tune.set or a scaleSets factor upstream
      // would simply be overwritten by the line above. This is the only hook on
      // a T2/T3 primary that survives.
      //
      // DELIBERATELY BREAKS THE TIER_DPS RELATIONSHIP for this one gun — that is
      // what a per-gun bump IS. Everything else on the ladder is unaffected:
      // each tier normalizes from `t1`, never from the previous tier, so unlike
      // clipMult (which feeds prevClip) this cannot propagate. If a whole class
      // needs moving, use CLASS_DAMAGE_MULT on its T1 instead and let
      // normalization carry it up — that keeps 1 / 1.5625 / 2.4414 intact.
      //
      // THE PaP FORM INHERITS IT EXACTLY ONCE, so never re-apply it in the isUp
      // branch: papApply reads the TUNED base (which carries override.damage)
      // and multiplies by PAP_UP. Same contract as RESERVE_ADD's note 2.
      if (gun.dmgMult && gun.dmgMult !== 1) {
        gun.override.damage = Math.round(gun.override.damage * gun.dmgMult);
        if (gun.override.minDamage !== undefined)
          gun.override.minDamage = Math.round(gun.override.minDamage * gun.dmgMult);
        console.log(`  tier ${gun.tier} ${gun.stem}: per-gun dmgMult x${gun.dmgMult} -> damage ${gun.override.damage}`);
      }
      console.log(`  tier ${gun.tier} ${gun.stem}: damage ${damage} -> ${dmg} (T1 ${t1.damage}@${t1.fireTime}s x${TIER_DPS[gun.tier]} at ${fireTime}s), clip ${clip} -> ${gun.override.clipSize} (floor ${floor})`);
      prevClip = gun.override.clipSize;
    }
  }
}

// ---- the SECONDARY ladder --------------------------------------------------
// Runs AFTER computeTierOverrides and is deliberately a separate pass: the two
// ladders share nothing but their DPS steps. computeTierOverrides `continue`s on
// every `secondary` gun so a sidearm can never become the T1 a primary line
// normalizes from, and this pass ignores every non-secondary for the same
// reason in reverse.
//
// WHAT IT DOES, per class: find the T1 reference DPS, then give each T2/T3 an
// override.damage equal to ref.damage x SEC_DPS[secTier] x (its own fireTime /
// ref.fireTime) — the identical formula the primary ladder uses, so a fast gun
// and a slow gun at the same tier land on the same damage-per-second rather
// than the same damage-per-shot.
//
// THE REFERENCE COMES FROM ONE OF TWO PLACES and the difference matters when
// you are reading a number that looks wrong:
//   * a MEASURED T1 (skirmisher, assault) — its tuned block is read exactly the
//     way computeTierOverrides reads a primary T1, so it already includes the
//     -25% SECONDARY_DMG_MULT and any tune.set on the gun.
//   * a DECLARED T1 (heavy, slasher) — SEC_T1_REF, because those two T1s are raw
//     ports with no generated block to measure. See the table's comment.
// A class with neither is a hard error, not a silent pass-through: a secondary
// emitted un-normalized would ship its raw port damage, and the raw ports here
// range from 20 (Klauser) to 7000 (RPG).
//
// NO never-shrink clip floor, on purpose. That rule exists so a PRIMARY
// promotion cannot shrink the magazine you just earned. Secondaries cross
// weapon classes between tiers by design (revolver -> shotgun, pistol ->
// launcher), where a monotonic clip is meaningless: the RPG's clip of 1 is the
// gun, not a downgrade.
function computeSecondaryOverrides() {
  for (const [cls, guns] of Object.entries(LADDER)) {
    const secs = guns.filter(g => g.secondary && g.enabled)
                     .sort((a, b) => a.secTier - b.secTier);
    if (!secs.length) continue;
    let ref = SEC_T1_REF[cls];
    const t1 = secs.find(g => g.secTier === 1);
    if (t1) {
      // measured, exactly as the primary T1 is
      const text = fs.readFileSync(t1.src, t1.encoding);
      const raw = extractBlock(text, t1.forms[0].srcAsset, t1.forms[0].gdf || t1.gdf);
      const tuned = raw.split(/\r?\n/).map(l => baseTune(t1, l, false)).join('\n');
      ref = { damage: readNum(tuned, 'damage'), fireTime: readNum(tuned, 'fireTime'),
              shot: readNum(tuned, 'shotCount') || 1 };
      console.log(`  sec T1 ${cls} ${t1.stem}: measured damage ${ref.damage} x${ref.shot} @ ${ref.fireTime}s`);
    } else if (ref) {
      console.log(`  sec T1 ${cls}: DECLARED ref damage ${ref.damage} @ ${ref.fireTime}s (raw-port T1, not measurable)`);
    }
    for (const gun of secs) {
      // TIER 1 IS NO LONGER SKIPPED. It used to be, because it WAS the ladder's
      // reference and shipped its own tuned value. The cap changed that: the
      // Bulldog measured 5,538 DPS against a MAC-10 doing 2,981, so the rung the
      // whole ladder was measured from was itself the worst offender.
      if (gun.secTier !== 1 && !ref) throw new Error(`secondary tier ${gun.secTier} (${gun.stem}) has no T1 reference for class ${cls} — add a SEC_T1_REF row or enable the T1`);
      const text = fs.readFileSync(gun.src, gun.encoding);
      const raw = extractBlock(text, gun.forms[0].srcAsset, gun.forms[0].gdf || gun.gdf);
      const tuned = raw.split(/\r?\n/).map(l => baseTune(gun, l, false)).join('\n');
      const damage = readNum(tuned, 'damage');
      const minDamage = readNum(tuned, 'minDamage');
      const fireTime = readNum(tuned, 'fireTime');
      // PELLETS ARE PART OF THE DPS, and this is the line that stops the
      // assault ladder shipping an 8x error. `damage` in a GDT is PER
      // PROJECTILE, so a shotgun at damage D does D x shotCount per pull. The
      // assault line normalizes a shotCount-8 shotgun (Mog 12, Executioner)
      // from a shotCount-1 revolver (Magnum) — without dividing by the gun's
      // own shotCount, each pellet got the whole revolver's damage and the
      // Mog 12 emitted 978 x 8 = 7,824 per shot against a T2 target of 978.
      // Caught on the first regen, 2026-08-24. The skirmisher line (shotgun
      // to shotgun) cancels out and is unaffected either way.
      const shot = readNum(tuned, 'shotCount') || 1;

      // ---- PASS 1: the ladder baseline -----------------------------------
      // T1 is its own baseline (it ships what it is tuned to); T2/T3 normalize
      // off it. This is what the gun WOULD ship with no cap, and it is the
      // number the cap clamps — never the raw port damage. Clamping the port
      // number instead would drop every under-cap gun to its unnormalized value
      // (the Klauser ships damage 20, the RPG 7000).
      let dmg = (gun.secTier === 1)
        ? damage
        : Math.round(ref.damage * ref.shot * SEC_DPS[gun.secTier] * fireTime / ref.fireTime / shot);
      const ladder = dmg;

      // ---- PASS 2: the ceiling -------------------------------------------
      const p = PRIMARY_T1[cls];
      let capDmg;
      if (p) {
        // CAP BASIS — p.capDps, recorded at the T1 site. It equals p.dps unless
        // the class has a CLASS_SEC_CAP_MULT entry pinning the ceiling above a
        // primaries-only knob (v14.32). Read capDps, never dps, or a
        // primary-only nerf drags every sidearm down with it.
        const capDps = (p.capDps !== undefined) ? p.capDps : p.dps;
        // primary DPS one tier below -> this gun's damage per projectile
        capDmg = Math.max(1, Math.round(capDps * SEC_CAP_REL[gun.secTier] * fireTime / shot));
        if (!SEC_CAP_ONLY || dmg > capDmg) dmg = capDmg;
      }
      const capped = capDmg !== undefined && dmg === capDmg && capDmg < ladder;

      // PER-GUN DAMAGE BUMP ON A SECONDARY — APPLIED AFTER THE CEILING, and the
      // order is the whole point. SEC_CAP_REL exists to stop a sidearm out-DPSing
      // the primary line, but an explicit per-gun instruction has to be able to
      // WIN over it or the knob is a silent no-op: clamp first, buff second.
      // Exactly the same argument as clipMult-after-the-clip-floor above.
      //
      // `dmg` itself is scaled, not just gun.override.damage, because the PaP
      // pin a few lines down derives from this local (Math.round(dmg * PAP_UP))
      // and minDamage derives from it too. Scaling only the override would leave
      // the Bulldog/Magnum pins on the pre-buff number.
      //
      // SPLASH IS SCALED SEPARATELY, IN baseTune — see the EXPLOSION_KEYS push
      // there. It has to be, because explosion damage never passes through this
      // normalization at all (EXPLOSION_KEYS is deliberately not in DAMAGE_KEYS),
      // and on a launcher the splash IS the damage. A dmgMult that moved only
      // `damage` would be a rounding error on the RPG.
      if (gun.dmgMult && gun.dmgMult !== 1) {
        dmg = Math.round(dmg * gun.dmgMult);
        console.log(`  sec ${gun.stem}: per-gun dmgMult x${gun.dmgMult} (after cap) -> damage ${dmg}`);
      }

      gun.override.damage = dmg;
      if (minDamage !== undefined && minDamage !== 0 && damage)
        gun.override.minDamage = Math.round(dmg * minDamage / damage);

      // SIDEARM CLIP (v16.12). computeTierOverrides skips secondaries before its
      // clipMult line, so a sidearm clipMult had no seat until now. Applied to the
      // TUNED base clip; the PaP form derives round(clip x PAP_UP) from this via
      // computePapSet, so base and PaP both move. No CLIP_STEP floor here - that
      // is a primary-ladder promise.
      if (gun.clipMult && gun.clipMult !== 1) {
        const clip = readNum(tuned, 'clipSize');
        if (clip) {
          gun.override.clipSize = Math.round(clip * gun.clipMult);
          console.log(`  sec ${gun.stem}: clipMult x${gun.clipMult} -> clipSize ${clip} -> ${gun.override.clipSize}`);
        }
      }

      // ---- the PaP pin, DERIVED not literal --------------------------------
      // The Bulldog and the Magnum pin their Pack-a-Punched damage in tune.setUp
      // (the Magnum also runs papKeepSource, which bypasses papApply outright),
      // so nothing downstream would carry a retune of the base onto their PaP
      // form — it would keep shipping the old hand-written literal. Rewriting
      // the pin here keeps PaP = base x PAP_UP for all twelve secondaries under
      // one rule. Guns that do not pin need nothing: papApply already derives
      // their PaP from this tuned base.
      if (gun.tune.setUp && gun.tune.setUp.damage !== undefined) {
        const before = gun.tune.setUp.damage;
        gun.tune.setUp.damage = Math.round(dmg * PAP_UP);
        if (gun.tune.setUp.minDamage !== undefined && gun.override.minDamage !== undefined)
          gun.tune.setUp.minDamage = Math.round(gun.override.minDamage * PAP_UP);
        console.log(`      PaP pin re-derived: ${before} -> ${gun.tune.setUp.damage} (base x${PAP_UP})`);
      }

      console.log(`  sec T${gun.secTier} ${gun.stem}: ${damage} -> ${dmg} x${shot} pellet(s)`
        + ` = ${Math.round(dmg * shot / fireTime)} DPS`
        + (capped ? `  CAPPED (ladder wanted ${ladder}, cap ${capDmg})` : `  (under cap ${capDmg})`));
    }
  }
}

// =============================================================================
// PACK III CAMO — THE TABLE-COPY LANE (v17.89, 2026-09-05; CAMO_PAP3_TABLE)
//
// User: "making one camo for the map ... sick and cyber colorful for 3rd pap".
// Every packed twin gets ITS OWN COPY of its port's weaponcamotable in which
// the base-121 sub-table is copied with ONE row changed per experiment slot:
//   index 123 (PACK III, TOD_PAP_CAMO_T3) -> tod_camo_pap3        our camo (tools/gen_tod_camo.js)
//   index 122                              -> mtl_origins_camo_alt  THE CONTROL: MadGaz's material, in this build for months
//   index 121 and every other row          -> untouched stock
// The other four sub-tables are listed by their ORIGINAL names, so PACK I (22)
// and PACK II (126) keep rendering exactly as they do today, and the port's
// base_material / camo_mask rows for THIS gun's model are byte-identical.
// Guns whose table has no base-121 sub-table (the two knives) or whose table
// is not defined in this install (the Leviathan) keep the port table. Read the
// result with the dev camo browser: 123 / 122 / 121 on a PACK III gun.
//
// PACK-A-PUNCH CAMO (v17.35, 2026-09-04) — one weaponcamo per gun, ours.
//
// Read the header of tools/gen_tod_camo.js for WHY this exists: the ports' own
// camo tables link fine but every material they name is a stock asset absent
// from the gdtDB, so all 124 of them resolve to nothing and every camo index —
// including stock's default 42 — has always been a no-op on this map. The fix
// is to point the `_up` forms at a table whose materials WE ship.
//
// The emitted asset keeps the port's own `base_material_*` / `camo_mask_*` rows
// (copied verbatim from that gun's ship table, both material parts): those name
// the materials on THIS gun's model and the masks that shape the camo over it,
// and getting them from anywhere but the port's own table would be guesswork.
// Only `_material` moves — to our three tier camos.
//
// SLOT 4 IS A CONTROL, deliberately. It points at `mtl_origins_camo_alt`, a
// MadGaz camo material that is ALREADY proven to link and render in this build
// (the Leviathan pulls it). If tiers 1-3 show nothing in game and slot 4 shows
// a camo, the fault is our material; if slot 4 is blank too, the fault is the
// pipeline. One build answers which — point TOD_PAP_CAMO_T1 at 4 in
// _tod_classes.gsc to look at it.
// =============================================================================
const CAMO_ENABLED = false;   // v17.58: the tod_camo_* tables were unreferenced since v17.50 (tiers ride stock slots on the port tables)
const CAMO_TIER_MATERIALS = ['tod_camo_pap1', 'tod_camo_pap2', 'tod_camo_pap3'];
const CAMO_CONTROL_MATERIAL = 'mtl_origins_camo_alt';

// THE COUNTRYSIDE CONTROL (v17.48 experiment, 2026-09-04). With the give lane
// PROVEN (the dev print reads `idx 3` on a bare MP7 — screenshot, 18:5x), the
// fault is downstream of the give: our material, or the camo mechanism on
// these twins. A sister map (countryside, docs/16 in map 1's KB) renders a
// camo on these same Skye packs using the PORT'S OWN table and stock index 28
// (`mtl_wpn_t7_camo_cwl` — slot 28 of every t5/t6/t9 ship table here). With
// this switch ON every _up twin KEEPS the port's table (our tod_camo_* tables
// are still emitted, unreferenced) and `_tod_classes::pap_camo_index` returns
// TOD_PAP_CAMO_STOCK_CONTROL in a dev build. One match then reads:
//   camo on the packed gun  -> mechanism + stock materials WORK; our table or
//                              material is the fault (and the "stub" theory
//                              of v17.35 is dead)
//   still bare              -> the mechanism itself is broken on the twins;
//                              stop touching art
// THE ANSWER IS IN (v17.50, same evening): "tier 1 works". The mechanism and
// the stock materials render; only our tod_camo_pap* materials never drew. So
// this flag is now the SHIPPED STATE, not an experiment: every _up twin keeps
// its port's camo table and _tod_classes' TOD_PAP_CAMO_T1..3 name three stock
// slots of it (28 / 42 / 22). The tod_camo_* tables below are still emitted
// but nothing references them; set CAMO_ENABLED = false at the next FULL
// build to drop them and their three materials + nine textures from the pack.
const CAMO_KEEP_PORT_TABLE = true;
const CAMO_PAP3_TABLE = true;              // v17.89: the table-copy lane above; a gun that got a copy points its _up forms at it
const CAMO_PAP3_MATERIAL = 'tod_camo_pap3';
const CAMO_PAP3_CONTROL = 'mtl_origins_camo_alt';
const CAMO_PAP3_INDEX = 124, CAMO_PAP3_CONTROL_INDEX = 122;   // LOCKSTEP: TOD_PAP_CAMO_T3 in _tod_classes.gsc is 124 (v17.91: 123 went back to stock Revelations 3 for PACK II)

// Where a gun's camo table is DEFINED when it is not in the gun's own source
// GDT. Resolved by name, never by scanning: the install's source_data is 1.1 GB
// across 438 GDTs and a full scan per run is not a thing to do every build.
const CAMO_TABLE_FILES = {
  't9_camo_ak47_table':      T9('skye_t9_ak-47.gdt'),        // gun.src is the .acc-orig copy
  'camo_t9_me_knife_combat': T9('t9_weapons/melee/wpn_t9_me_knife_combat.gdt'),
  'camo_t9_me_wakizashi':    T9('t9_weapons/melee/wpn_t9_me_wakizashi.gdt'),
  'skye_up_camo':            T9('skye_up_camo.gdt'),   // the Bulldog's, and the
                                                       // ports' generic PaP set
};

const camoAsset = (stem) => `tod_camo_${stem}`;
const camoEmitted = new Set();   // stems that got a table — the ONE authority
                                 // for whether a variant's camo field is rewritten

function tryBlock(text, asset, gdf) {
  try { return extractBlock(text, asset, gdf); } catch (e) { return null; }
}

// the camo table named by a gun's source block, if any
function sourceCamoName(block) {
  const m = block.match(/^\s*"camo"\s+"([^"]+)"\s*$/m);
  return m && m[1] ? m[1] : null;
}

// find a weaponcamo/weaponcamotable asset's text, wherever it lives
function camoAssetText(name, ownText) {
  for (const text of [ownText, ...(CAMO_TABLE_FILES[name] && fs.existsSync(CAMO_TABLE_FILES[name])
        ? [fs.readFileSync(CAMO_TABLE_FILES[name], 'utf8')] : [])]) {
    if (!text) continue;
    const tbl = tryBlock(text, name, 'weaponcamotable.gdf');
    if (tbl) {
      // a table is a list of weaponcamo tables; slot 1 is the SHIP set, which is
      // the one whose base materials/masks cover the gun's own model
      const ship = tbl.match(/^\s*"table_01_name"\s+"([^"]+)"\s*$/m);
      if (!ship || !ship[1]) return null;
      return camoAssetText(ship[1], text);
    }
    const camo = tryBlock(text, name, 'weaponcamo.gdf');
    if (camo) return camo;
  }
  return null;
}

// slot 1 of every material PART, as `key -> value` rows keyed without the slot
function slotOneRows(camoBlock) {
  const parts = new Map();   // part number -> [ [suffix, value], ... ]
  for (const line of camoBlock.split(/\r?\n/)) {
    const m = line.match(/^\s*"material(\d+)_1_([A-Za-z0-9_]+)"\s+"(.*)"\s*$/);
    if (!m) continue;
    if (!parts.has(m[1])) parts.set(m[1], []);
    parts.get(m[1]).push([m[2], m[3]]);
  }
  return parts;
}

function buildCamoBlock(stem, parts) {
  const slots = [...CAMO_TIER_MATERIALS, CAMO_CONTROL_MATERIAL];
  const out = [`\t"${camoAsset(stem)}" ( "weaponcamo.gdf" )`, '\t{',
               '\t\t"baseIndex" "1"', '\t\t"configstringFileType" "WEAPONCAMO"'];
  for (const [part, rows] of [...parts.entries()].sort()) {
    for (let s = 0; s < slots.length; s++) {
      for (const [key, value] of rows)
        out.push(`\t\t"material${part}_${s + 1}_${key}" "${key === 'material' ? slots[s] : value}"`);
    }
  }
  out.push(`\t\t"numCamos" "${slots.length}"`, '\t\t"type" "weaponcamo"', '\t}');
  return out.join('\n');
}

// the text a weaponcamotable / weaponcamo asset lives in — the gun's own GDT or the table file map
function camoTextsFor(name, ownText) {
  const out = [ownText];
  if (CAMO_TABLE_FILES[name] && fs.existsSync(CAMO_TABLE_FILES[name])) out.push(fs.readFileSync(CAMO_TABLE_FILES[name], 'utf8'));
  return out;
}
function findIn(texts, asset, gdf) { for (const t of texts) { const b = tryBlock(t, asset, gdf); if (b) return b; } return null; }

// THE TABLE-COPY LANE (v17.89). Returns [tableBlock, subTableBlock, tableName] or null.
function buildPap3Copy(stem, tableName, ownText) {
  const texts = camoTextsFor(tableName, ownText);
  const table = findIn(texts, tableName, 'weaponcamotable.gdf');
  if (!table) return null;                                     // names a weaponcamo directly, or undefined here
  const entries = [...table.matchAll(/^\s*"(table_\d\d_name)"\s+"([^"]+)"\s*$/gm)].map(m => [m[1], m[2]]);
  let hit = null;
  for (const [key, asset] of entries) {
    const sub = findIn(texts, asset, 'weaponcamo.gdf');
    if (!sub) continue;
    const bi = sub.match(/^\s*"baseIndex"\s+"(\d+)"\s*$/m);
    if (bi && parseInt(bi[1], 10) === 121) { hit = { key, asset, sub }; break; }
  }
  if (!hit) return null;                                       // no base-121 sub-table (the knives)
  const slotOf = idx => idx - 121 + 1;
  const subName = 'tod_camo_' + stem + '_base121', tableCopy = 'tod_camo_' + stem + '_table';
  // header renames and row swaps are done with replacer FUNCTIONS: a string replacement
  // treats $-sequences specially, and a GDT row's regex ends in "$" (2026-09-05, this file's own prefix
  // was spliced into this function twice by a patch that forgot that)
  let sub = hit.sub.replace('"' + hit.asset + '" ( "weaponcamo.gdf" )', () => '"' + subName + '" ( "weaponcamo.gdf" )');
  let moved = 0;
  for (const [idx, mat] of [[CAMO_PAP3_INDEX, CAMO_PAP3_MATERIAL], [CAMO_PAP3_CONTROL_INDEX, CAMO_PAP3_CONTROL]]) {
    const re = new RegExp('^(\\s*)"material1_' + slotOf(idx) + '_material"\\s+"[^"]*"\\s*$', 'm');
    if (!re.test(sub)) throw new Error(stem + ': ' + hit.asset + ' has no material1_' + slotOf(idx) + '_material row');
    sub = sub.replace(re, (m0, indent) => indent + '"material1_' + slotOf(idx) + '_material" "' + mat + '"'); moved++;
  }
  if (moved !== 2) throw new Error(stem + ': expected 2 rows moved, got ' + moved);
  let tbl = table.replace('"' + tableName + '" ( "weaponcamotable.gdf" )', () => '"' + tableCopy + '" ( "weaponcamotable.gdf" )');
  tbl = tbl.replace(new RegExp('^(\\s*)"' + hit.key + '"\\s+"' + hit.asset + '"\\s*$', 'm'), (m0, indent) => indent + '"' + hit.key + '" "' + subName + '"');
  if (!tbl.includes('"' + subName + '"')) throw new Error(stem + ': table entry swap failed');
  return [tbl, sub, tableCopy];
}
const camoTableOf = new Map();   // stem -> the table copy its _up forms should name

// rewrite an _up variant's camo field onto our table
function camoSet(gun, line) {
  if (CAMO_PAP3_TABLE && camoTableOf.has(gun.stem))
    return line.replace(/^(\s*)"camo"\s+"[^"]*"\s*$/, `$1"camo" "${camoTableOf.get(gun.stem)}"`);
  if (CAMO_KEEP_PORT_TABLE) return line;   // the countryside control — see the flag
  if (!camoEmitted.has(gun.stem)) return line;
  return line.replace(/^(\s*)"camo"\s+"[^"]*"\s*$/, `$1"camo" "${camoAsset(gun.stem)}"`);
}

// ---- generate --------------------------------------------------------------
computeTierOverrides();
computeSecondaryOverrides();

const allGuns = Object.values(LADDER).flat().filter(g => g.enabled);
allGuns.sort((a, b) => {
  const ia = EMIT_ORDER.indexOf(a.stem), ib = EMIT_ORDER.indexOf(b.stem);
  return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
});

const blocks = [];
const zoneLines = [];
const csvRows = [];
const emittedNames = new Set();
let total = 0;
let nCamoTables = 0;

for (const gun of allGuns) {
  const text = fs.readFileSync(gun.src, gun.encoding);
  // per-FORM: the dark rung exists on the packed form only (axisMaxUp).
  // PaP stat set from the TUNED base form (base tune + tier overrides; the
  // level-0 ladder is the identity) BEFORE any _up variant is generated.
  computePapSet(gun.stem, extractBlock(text, gun.forms[0].srcAsset, gun.forms[0].gdf || gun.gdf)
    .split(/\r?\n/).map(l => baseTune(gun, l, false)).join('\n'));

  // PaP CAMO — build this gun's own table BEFORE any variant is emitted, so
  // camoSet() below knows whether it has one to point at. A gun whose source
  // names no camo table (or whose table is not in this install — the Leviathan's
  // is referenced by every port that uses it and DEFINED by none) simply keeps
  // what it had: no camo, exactly as it ships today.
  if (CAMO_PAP3_TABLE) {
    const upForm = gun.forms.find(f => f.up) || gun.forms[0];
    const srcName = sourceCamoName(extractBlock(formText(gun, upForm, text), upForm.srcAsset, upForm.gdf || gun.gdf));
    const copy = srcName ? buildPap3Copy(gun.stem, srcName, text) : null;
    if (copy) { blocks.push(copy[0], copy[1]); camoTableOf.set(gun.stem, copy[2]); nCamoTables++; }
    else console.log(`  camo: ${gun.stem} keeps ${srcName || '(no table)'} — ${srcName ? 'no base-121 sub-table resolvable here' : 'no camo field'}`);
  }
  if (CAMO_ENABLED) {
    const upForm = gun.forms.find(f => f.up) || gun.forms[0];
    const srcName = sourceCamoName(extractBlock(formText(gun, upForm, text), upForm.srcAsset, upForm.gdf || gun.gdf));
    const camoText = srcName ? camoAssetText(srcName, text) : null;
    const parts = camoText ? slotOneRows(camoText) : null;
    if (parts && parts.size) {
      blocks.push(buildCamoBlock(gun.stem, parts));
      camoEmitted.add(gun.stem);
    } else if (srcName) {
      console.log(`  camo: ${gun.stem} SKIPPED — ${srcName} not resolvable in this install`);
    }
  }

  for (const form of gun.forms) {
    const variants = variantsOf(gun, form.up);
    // form.gdf overrides gun.gdf — the Executioner's PaP half is declared
    // under dualwieldweapon.gdf while its base is a bulletweapon. Without
    // this, extractBlock looks for the wrong decl and throws.
    const block = extractBlock(formText(gun, form, text), form.srcAsset, form.gdf || gun.gdf);
    for (const v of variants) {
      const name = form.name(v.suffix);
      // form.str( suffix ) — PER-FORM string overrides, applied last. gun.tune.str
      // cannot do this job: it writes the SAME value to every form, and the one
      // thing that needs writing here differs between them by construction — each
      // half of a dual-wield PaP has to name the OTHER half.
      const { text: twin, scaled } = makeVariant(block, form.srcAsset, name, form.gdf || gun.gdf,
        (line) => {
          let l = ladderScale(gun, baseTune(gun, line, form.up), v.levels);
          if (form.str) l = strSet(l, form.str(v.suffix));
          if (form.up) l = camoSet(gun, l);   // PaP forms only — a base gun wears no camo
          return l;
        });
      // Quivers store absolute arrows, unlike magazine-relative gun reserves.
      // Start full at every mag/PaP rung; never add a phantom reserve magazine.
      let emittedTwin = gun.nativeQuiver ? twin.replace(/"startAmmo" "[^"\n]*"/, '"startAmmo" "' + readNum(twin, 'clipSize') + '"') : twin;
      // FALLOFF FOLLOWS DAMAGE (2026-09-25, user: fix the "backwards shotgun falloff").
      // Only `damage`/`minDamage` were ever rewritten; damage2..5 kept the PORT's
      // values, so a gun whose point-blank damage was normalized DOWN hit harder at
      // mid range (Bulldog 27 -> 95, SG12 41 -> 230, 870 PaP 356 -> 420). Scale the
      // whole curve by the same factor so each gun keeps its own shape.
      {
        const srcD = readNum(block, 'damage'), outD = readNum(emittedTwin, 'damage');
        if (srcD && outD && srcD !== outD) {
          const k = outD / srcD;
          for (const key of ['damage2', 'damage3', 'damage4', 'damage5']) {
            const sv = readNum(block, key);
            if (sv) emittedTwin = emittedTwin.replace(new RegExp(`"${key}" "[^"\\n]*"`), `"${key}" "${Math.max(1, Math.round(sv * k))}"`);
          }
        }
      }
      if (scaled === 0) throw new Error(`no fields scaled for ${name} — key set mismatch?`);
      blocks.push(emittedTwin);
      zoneLines.push(`weapon,${name}`);
      emittedNames.add(name);
      total++;
    }
  }
  // CSV rows: base-variant -> up-variant, so PaP works.
  //
  // THE NAMES MUST COME FROM form.name(), NOT be re-spelled here. This block
  // used to hardcode the up name as stem + '_up' + suffix, which is right for
  // most ports and WRONG for any whose PaP asset carries a trailing suffix: the
  // Enfield's up-form is t5_enfield_up_r0m0_zm and all three blades are
  // <stem>_up_k<N>_zm. Those four stems advertised an upgrade_name that existed
  // nowhere, and stock PaP silently refused every one of them — the entire
  // SLASHER class plus the assault T1 gun could not be Pack-a-Punched (user
  // 2026-08-23: "why couldnt i pap my enfield"). form.name() is the same
  // function that writes the zone line and the GDT block name, so the three
  // can no longer disagree.
  const fBase = gun.forms.find(f => !f.up), fUp = gun.forms.find(f => f.up);
  if (!fBase) throw new Error(`${gun.stem}: needs a base form`);
  // A GUN WITH NO PACKED FORM GETS NO UPGRADE ROW, AND THAT IS THE POINT.
  // Every row in this table means "this gun packs into that gun", so a gun
  // that packs into nothing has nothing to say here. Stock can_upgrade then
  // refuses it at the machine, which is exactly the intent for the MAGE staff
  // (user 2026-09-07: "let's not let it [PaP]").
  //
  // THIS USED TO THROW. The assertion was right for every gun that had ever
  // existed here -- all of them packed -- but it encoded "no upgrade row" as
  // impossible rather than as a case. It is a case now.
  //
  // THE CLASS-GUN PaP LANE IS UNAFFECTED: zm_cwpap.gsc buys class primaries
  // through its own path precisely BECAUSE they fail stock can_upgrade by
  // roster design, and that path only sets player.tod_pap_owned. It never
  // consults this table.
  if (!fUp) {
    console.log(`  ${gun.stem}: base-only, no PaP form -> no weapons-table upgrade row`);
    continue;   // CONTINUE, NOT RETURN: this block is inside a top-level
                // `for (const gun of allGuns)`, not a function. A `return` here
                // ends the MODULE -- the run exits 0 with the ledger never
                // printed and the emit phase never reached. Cost one run to find.
  }
  // ...then STRIP a trailing "_zm": the engine drops that suffix, so the script
  // name and the weapons-table name are the asset name without it. See the
  // evidence block in _tod_classes.gsc register_guns — writing the tailed name
  // here is what broke the blades on 2026-08-23.
  const scriptName = n => n.replace(/_zm$/, '');
  // THE BASE SET, DELIBERATELY (v17.10). Each row is "this gun packs into that
  // gun", so it must be keyed on variants that EXIST unpacked. Since the dark
  // rungs are packed-only (axisMaxUp), the two sets are different sizes now, and
  // iterating the packed set would pair a base variant with a DARK packed one —
  // Pack-a-Punch would hand out the dark gun to anyone who bought a pack.
  //
  // Dark-only variants therefore get no row, which is correct: they are only
  // ever reached by a player who is ALREADY packed, reconcile_twin swaps them in
  // directly by asset name, and this map's is_weapon_upgraded check pairs the
  // table lookup with IsSubStr(name, "_up") — which a dark name satisfies.
  for (const v of variantsOf(gun, false)) {
    const b = scriptName(fBase.name(v.suffix)), u = scriptName(fUp.name(v.suffix));
    const c = gun.csv;
    csvRows.push(c.melee
      ? `${b},${u},,${c.cost},${c.vo},,,,,FALSE,FALSE,FALSE,,,FALSE,FALSE,${c.cls},,,`
      : `${b},${u},,${c.cost},${c.vo},,,,,FALSE,FALSE,FALSE,,,FALSE,TRUE,${c.cls},,,`);
  }
}

// GUARD (2026-08-23): every name the weapons table advertises must be an asset
// this run actually emitted. The Enfield/blade PaP bug survived weeks because
// nothing cross-checked the CSV against the zone list — the map built clean,
// linked clean, and only failed at the PaP machine in game. Cheap check, and it
// fails the BUILD instead of the playthrough.
{
  const missing = [];
  for (const row of csvRows) {
    const parts = row.split(",");
    // an emitted asset may carry a trailing "_zm" the script name drops
    const linked = n => emittedNames.has(n) || emittedNames.has(n + "_zm");
    if (!linked(parts[0])) missing.push("base " + parts[0]);
    if (!linked(parts[1])) missing.push("upgrade " + parts[1]);
  }
  if (missing.length)
    throw new Error("weapons CSV references " + missing.length + " name(s) with no emitted asset:" + String.fromCharCode(10) + "  " + missing.join(String.fromCharCode(10) + "  "));
  console.log("  csv/zone cross-check OK (" + csvRows.length + " rows, every base + upgrade name is an emitted asset)");
}

// GUARD (2026-08-24): every DualWieldWeapon reference must resolve to an asset
// this run emitted, REMEMBERING THAT THE ENGINE APPENDS "_zm" TO THE FIELD.
// This is the check that would have caught the Executioner before it shipped:
// its halves were emitted as t6_executioner_rdw_up_b / _ldw_up_b and named each
// other correctly, so every existing cross-check passed — but the engine went
// looking for "<field>_zm", found nothing, and aborted the map load with
// "Com_ERROR: could not find alt dualwield". The map built clean and linked
// clean; the only symptom was a map that would not load.
//
// Both directions matter: the field must not carry _zm (the AMP63's 2026-08-23
// failure) and the asset it points at must (the Executioner's, 2026-08-24).
{
  const bad = [];
  for (const block of blocks) {
    const name = (block.match(/^\t"([A-Za-z0-9_]+)" \( "[a-z]+\.gdf" \)/m) || [])[1];
    const m = block.match(/"DualWieldWeapon"\s+"([A-Za-z0-9_]*)"/);
    if (!name || !m || !m[1]) continue;               // blank = not dual wield
    if (/_zm$/.test(m[1]))
      bad.push(name + ' names "' + m[1] + '" — the field must NOT carry _zm, the engine appends it');
    // The "_zm" asset is the ONLY valid resolution — do not also accept the bare
    // name as a fallback. Accepting it is what made the first version of this
    // guard pass the exact bug it was written to catch: with both halves emitted
    // WITHOUT _zm they satisfied each other, while the engine still resolved
    // "<field>_zm" and found nothing.
    else if (!emittedNames.has(m[1] + "_zm"))
      bad.push(name + ' names "' + m[1] + '" -> engine resolves "' + m[1] + '_zm", which nothing emitted');
  }
  if (bad.length)
    throw new Error("dual-wield cross-reference is broken (the map will not load):" + String.fromCharCode(10) + "  " + bad.join(String.fromCharCode(10) + "  "));
  console.log("  dual-wield cross-check OK");
}

// GUARD (2026-08-24): A PACK-A-PUNCHED SECONDARY MUST OUT-DAMAGE ITS OWN BASE.
// Written because the opposite shipped. When the secondary nerf was applied to
// DAMAGE_KEYS in baseTune's isUp branch it double-counted against every PaP form
// that derives through papApply, landing them all at 1.25 x 0.75 = 0.9375 of
// base: the RPG at 563 -> 528, the Nail Gun 460 -> 431, the SG12 138 -> 130.
// Nothing caught it. The build was clean, the linker was clean, the ledger was
// clean, and the only way to notice was to Pack-a-Punch a sidearm in game and
// feel it get worse.
{
  const dmgOf = {};
  for (const block of blocks) {
    const n = (block.match(/^\t"([A-Za-z0-9_]+)" \( "[a-z]+\.gdf" \)/m) || [])[1];
    const d = block.match(/"damage"\s+"(-?\d+(?:\.\d+)?)"/);
    if (n && d) dmgOf[n] = parseFloat(d[1]);
  }
  const bad = [];
  for (const gun of allGuns) {
    if (!gun.secondary || gun.melee) continue;
    const fBase = gun.forms.find(f => !f.up), fUp = gun.forms.find(f => f.up);
    if (!fBase || !fUp) continue;
    for (const v of variantsOf(gun)) {
      const b = dmgOf[fBase.name(v.suffix)], u = dmgOf[fUp.name(v.suffix)];
      if (b === undefined || u === undefined) continue;
      if (u <= b)
        bad.push(`${gun.stem}${v.suffix}: PaP ${u} <= base ${b} — Pack-a-Punch makes this gun WORSE`);
    }
  }
  if (bad.length)
    throw new Error("secondary PaP is not an upgrade:" + String.fromCharCode(10) + "  " + bad.join(String.fromCharCode(10) + "  "));
  console.log("  secondary PaP-beats-base check OK");
}

// ---- the ledger — GUARDS THE WRITES, AND MUST STAY ABOVE THEM ---------------
// MOVED HERE 2026-09-01. It used to sit AFTER all three writeFileSync calls, so
// a run that exceeded the guard had ALREADY rewritten the weapon GDT, the zpkg
// and the weapons CSV before it threw. "It throws" therefore did not mean "it
// did nothing" — a guard that runs after the writes is not a guard on the
// writes, it is a report. That fired for real: an over-budget run at 01:36 on
// 2026-09-01 left all three outputs rewritten (harmlessly, because the
// generator is deterministic and the inputs had not changed — but the next
// person to edit an axis and run this would have been left holding an
// over-budget tree that still looked generated).
//
// It also means the ledger NUMBER can now be read without mutating anything:
// run the generator, read the printed figure, and if it throws nothing on disk
// has moved. That is what makes "what would HANDLING at 4 tiers cost?" a
// question you can answer instead of estimate.
//
// KEEP THIS ABOVE THE writeFileSync CALLS. `total` is final long before this
// point (nothing mutates it after the generation loop) and
// countFixedRegistrations() deliberately skips OUT_ZPKG, so neither depends on
// the writes having happened.
const LEDGER_FIXED = countFixedRegistrations();
const ledger = total + LEDGER_FIXED;
console.log(`PACK III CAMO TABLES: ${nCamoTables} gun(s) got a table copy (index ${CAMO_PAP3_INDEX} -> ${CAMO_PAP3_MATERIAL}, ${CAMO_PAP3_CONTROL_INDEX} -> ${CAMO_PAP3_CONTROL})`);
console.log(`REGISTRATION LEDGER: ${total} generated + ${LEDGER_FIXED} fixed = ${ledger}  (guard ${LEDGER_GUARD}; map 1 shipped a BOOTING 229-asset table, 368 = boot-AV)`);
if (ledger > LEDGER_GUARD) throw new Error(`ledger ${ledger} exceeds the ${LEDGER_GUARD} guard — NOTHING WAS WRITTEN. Retire an axis or a gun before adding more.`);

// Idempotent CSV patch — NO marker/comment lines (the weapon-table parser
// reads every line as a row; a "## comment" row would feed GetWeapon garbage).
// Strip every row that LOOKS like a generated variant of ANY ladder stem
// (enabled or not — a gun that was disabled again must lose its rows), then
// append the current set. Variant rows = <stem>(_up)?(_<letter><digit>...|_b),
// Retired stems: their old rows must still be swept. (The sort sat INSIDE this
// comment from 2026-09-20 until docs/157; harmless - the anchored regex
// backtracks through every alternative - but it is back where it was meant to be.)
const stems = Object.values(LADDER).flat().map(g => g.stem)
  .concat(["t9_me_knife_american", "t9_mac10", "t9_stoner63", "t6_msmc", "t9_mp5", "t6_mp7",
           "t6_mk48", "t5_hk21", "t6_death_machine", "cc_car", "t5_enfield", "t9_krig6", "t9_ak47", "t9_me_baseballbat", "t9_me_wakizashi", "leviathan"])   // docs/157: the retired heavy ladder
  .sort((a, b) => b.length - a.length);
// The optional `(?:_zm)?` is load-bearing (co-op audit 2026-08-23). Without it
// the tail after the ladder suffix had to be the comma itself, so a row written
// in the `_zm`-suffixed era — `t9_me_knife_american_k0_zm,` — never matched
// (`_z` is not `[a-z]\d`). Those rows survived every purge AND the current set
// was appended beside them, so each regen added 18 duplicate blade rows: the
// CSV was observed growing 145 -> 163 lines with 18 duplicated column-0 names.
// The stale rows name assets that no longer exist, which is harmless only for
// as long as nothing looks them up — the day a blade is retired or re-laddered,
// a GetWeapon() on a dead name at level init is the frontend-dump case.
// RETIRED STEMS (2026-09-26): a gun that LEFT the ladder is not in `stems`, so
// its rows would survive this purge forever. The Skirmisher's three guns left
// with the class (the Necromancer replaced it).
// The Warrior's Hellbound knives and sword left on 2026-09-26 (punch / gauntlet took their rungs).
const RETIRED_STEMS = ['cc_saug', 'cc_m1927', 'cc_r99', 'cc_twin_knives', 'cc_plain_sword'];
const variantRe = new RegExp(`^(?:${stems.concat(RETIRED_STEMS).map(s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})(?:_up)?(?:_(?:[a-z]\\d)+|_b)(?:_zm)?,`);
let csv = fs.readFileSync(CSV, 'utf8');
// These inherited stock gun rows are unobtainable here: Tower has no
// wallbuys/box and its gun classes use generated variants. Keep utility,
// wonder-weapon, starting-pistol and explicitly imported rows intact.
const unusedStockCostRows = new Set([
  'ar_accurate', 'ar_cqb', 'ar_damage', 'ar_longburst', 'ar_marksman', 'ar_standard',
  'lmg_cqb', 'lmg_heavy', 'lmg_light', 'lmg_slowfire', 'pistol_burst', 'pistol_fullauto',
  'shotgun_fullauto', 'shotgun_precision', 'shotgun_pump', 'shotgun_semiauto',
  'smg_burst', 'smg_capacity', 'smg_fastfire', 'smg_standard', 'smg_versatile',
  'sniper_fastbolt', 'sniper_fastsemi', 'sniper_powerbolt', 'smg_sten', 'ar_famas',
  'ar_garand', 'smg_mp40', 'smg_ppsh', 'ar_peacekeeper', 'pistol_energy',
  'shotgun_energy', 'smg_thompson',
]);
csv = csv.split(/\r?\n/).filter(l => !variantRe.test(l) && !unusedStockCostRows.has(l.split(',')[0])).join('\n');
if (!csv.endsWith('\n')) csv += '\n';
csv += csvRows.join('\n') + '\n';
const costBudget = require('./verify_weapon_costs').verifyWeaponCosts(csv);
console.log(`WEAPON COST TABLE: ${costBudget.costs}/240 entries (separate from asset registrations)`);

// latin1 superset of ascii — safe for the mixed sources
fs.writeFileSync(OUT_GDT, '{\n' + blocks.join('\n') + '\n}\n', 'latin1');
console.log(`wrote ${OUT_GDT}  (${total} variant weapon assets)`);

fs.writeFileSync(OUT_ZPKG, [
  '// GENERATED by tools/gen_tod_twins.js — twin-swap weapon variants.',
  '// Included from zm_tod2_cybercity.zone via `include,tod_twins`.',
  ...zoneLines, '',
].join('\n'));
console.log(`wrote ${OUT_ZPKG}  (${zoneLines.length} weapon lines)`);

fs.writeFileSync(CSV, csv);
console.log(`patched ${CSV}  (${csvRows.length} PaP-mapping variant rows, marker-free)`);
