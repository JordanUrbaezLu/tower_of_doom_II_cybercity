# Upgrade card numbers (domain ids)

Every upgrade card has a number (its domain id). The HUD receives that number
over a 6-bit field, so the only numbers that exist are 1..63. As of 2026-09-26
all 63 were assigned (Breacher 58-61, Warrior 62-63); since 2026-10-04 the
Mage's ids 49-56 are free again (the class was retired whole). Widening the
field is not an option: the clientuimodel pool is at its proven ceiling.

**The user's decision (2026-09-26): a new card REUSES a retired card's number.**

## Free numbers

A number is free when no live `add_domain` uses it. Claim one here, in the same
edit that uses it, so two sessions never take the same one.

| Id | Retired card | Old pause plate still zoned? | Claimed by |
|---|---|---|---|
| 5  | SPRINT (sprint) - retired 2026-09-26 (user: off the Warrior + Necromancer; no class held it after); the SPRINT card came back 2026-09-27 as the Archer's on id 29 | no | NECROMANCER reaperreach (REAPER'S REACH) - class build card, 2026-09-27 |
| 1  | DAMAGE (damage) - retired 2026-09-27 (user: each class gets its own core weapon card instead) | yes (r01) | |
| 6  | HEADSHOT (headshot) | no | ARCHER deadeye (DEADEYE, core weapon card, 2026-09-27) |
| 7  | MAG SIZE (magsize) | no | WARRIOR heavyhands (HEAVY HANDS, core weapon card, 2026-09-27) |
| 9  | MOBILITY (mobility); then JUGGERNAUT (juggernaut), retired 2026-09-27 class pass 2 | yes (r09) | NECROMANCER cloak (INVISIBILITY CLOAK, tactical, 9 levels) - class pass 2, 2026-09-27 |
| 10 | BULLET FEED (bulletfeed) | no | (free again: PACK MASTER retired 2026-09-27 class pass 4) |
| 11 | ECHO ROUNDS (echo) | yes (r11) | |
| 12 | REGEN (regen); then EXECUTIONER (executioner), retired 2026-09-27 class pass 2 | yes (r12) | WARRIOR demonslayer (DEMON SLAYER, 9 levels) - class pass 2, 2026-09-27 |
| 17 | RECOIL (recoil) | no | NECROMANCER soulsiphon (SOUL SIPHON) - class build card, 2026-09-27; PARKED in class pass 2 (the 12-row cap), key stays mapped |
| 18 | MELEE SPEED (knifespeed) - retired 2026-09-27 into HEAVY HANDS (its "k" swing forms stay, driven by heavyhands) | yes (r18) | |
| 19 | PENETRATION (penetration); then BURNED OUT (burnedout), retired 2026-09-27 class pass 2 (the Necromancer passive now) | no | NECROMANCER summonmaster (SUMMONER MASTER, 9 levels) - class pass 2, 2026-09-27 |
| 22 | CHAIN LUNGE (lunge) | yes (r22) | |
| 26 | OVERDRIVE (overdrive) | no | ARCHER pierce (PIERCING) - 2026-09-27 class pass 3 (was HUNTER'S MARK, retired the same day) |
| 27 | KILL RELOAD (killreload) | yes (r27) | |
| 28 | IMPACT ROUNDS (impact) | yes (r28) | |
| 29 | SUPPRESSING FIRE (suppress); then AERIALIST (aerialist), retired 2026-09-27 class pass 2 | no | ARCHER sprint (SPRINT, 9 levels; the key "sprint" moved here from 5) - class pass 2, 2026-09-27 |
| 30 | MEAT GRINDER (grinder) | yes (r30) | |
| 31 | FREE again: MELEE RANGE (meleerange) RETIRED 2026-09-28 (user: "move melee range upgrade inside of arms specialist"; its reach is ARMS SPECIALIST's, id 7; add_domain commented, Lua rows commented, domain_id kept mapped). History: CLAIMED 2026-09-26 by the Warrior (live from build 13; add_domain + domain_id + Lua rows in): crowd-sweep reach +15%/Lv, max 5 (6 since class pass 2, 2026-09-27), band A, slasher, no dark, class scope; was DRAW CUT (drawcut), retired 2026-09-26 (Warrior card cut #2) | no | text fallback until art |
| 32 | SPRINT ARMOR (sprintarmor) | yes (r32) | |
| 34 | MOMENTUM (momentum) | yes (r34) | |
| 35 | GIANT SLAYER (bossdmg) | no | ARCHER shotspeed (QUICK DRAW, was SHOT SPEED) - 2026-09-27 class pass 4 (was SHADOWSTEP) |
| 36 | BACK ARMOR (backarmor); then POINT BLANK (pointblank), retired 2026-09-27 class pass 2 | no | BREACHER fusion (EXPLOSIVE FUSION, 9 levels) - class pass 2, 2026-09-27 |
| 37 | FORCED MARCH (march); then DEMOLITIONIST (demolition), retired 2026-09-27 class pass 2 | no | WARRIOR vitality (VITALITY, 6 levels; the key "vitality" moved here from 38) - class pass 2, 2026-09-27 |
| 38 | VITALITY (vitality) - the key moved to id 37 on 2026-09-27 | no | NECROMANCER summonpower (2026-09-26) |
| 39 | RECOVERY (recovery) | no | NECROMANCER soulbeam (2026-09-26); displayed SOUL SUCK since 2026-09-27 (text card: the soul_beam art bakes the old name) |
| 40 | PERK SLOTS (perkslots) - retired 2026-09-27 (user: "no perk limit on this map"; the limit is 16) | yes (r40) | |
| 42 | FULL STEAM (lmgsprint) | no | (free again: BULWARK retired 2026-09-27 class pass 3) |
| 47 | DEADSHOT (deadshot) | no | |
| 48 | AIR (mage_air) | no | WARRIOR sweep (CLEAVE) - 2026-09-27 class pass 4 (was BATTLE RHYTHM) |
| 49 | FIRE BLAST (mage_fire) - retired 2026-10-04 with the Mage; no domain_id case left; usable like a brand-new id | no (archived) | |
| 50 | ICE SHATTER (mage_ice) - retired 2026-10-04 with the Mage; no domain_id case left; usable like a brand-new id | no (archived) | |
| 51 | ATTUNEMENT (mage_attune) - its domain_id case was deleted 2026-10-04 with the Mage; usable like a brand-new id | no (archived 2026-10-04) | |
| 52 | HEALING AURA (mage_heal) - retired 2026-10-04 with the Mage; no domain_id case left; usable like a brand-new id | no (archived) | |
| 53 | CHAIN LIGHTNING (mage_bolt) - retired 2026-10-04 with the Mage; no domain_id case left; usable like a brand-new id | no (archived) | |
| 54 | ARCHMAGE (mage_arch) - retired 2026-10-04 with the Mage; no domain_id case left; usable like a brand-new id | no (archived) | |
| 55 | BLINK (mage_blink) - retired 2026-10-04 with the Mage; no domain_id case left; usable like a brand-new id | no (archived) | |
| 56 | MYSTICAL HANDS (mage_quickhands) - retired 2026-10-04 with the Mage; no domain_id case left; usable like a brand-new id | no (archived) | |
| 59 | EXPLOSIVES (never shipped; the Breacher cut it 2026-09-26, no slug, no plate, no domain_id case: usable like a brand-new id) | no | NECROMANCER soulbomb (2026-09-26) |

**CLASS PASS 2 (2026-09-27)**: the six cards retired that day (AERIALIST, POINT BLANK,
DEMOLITIONIST, EXECUTIONER, JUGGERNAUT, BURNED OUT) handed their ids straight to the six new
ones in the same edit (table above); BATTLE RHYTHM's 48 is free again. The two cards whose
KEYS came back to life (sprint, vitality) moved to fresh ids because their old ones (5, 38)
were already reused - a live key may never share an id with another live key.

Regenerate this list when in doubt: every id in `_tod_upgrade_ui.gsc`
`domain_id()` whose key has no live `add_domain` call, plus every id in 1..63
with no `case` at all (49-56 since the Mage was retired).

## Reuse checklist (all in ONE edit)

1. **GSC id.** In `_tod_upgrade_ui.gsc` `domain_id()`, ADD `case "<newkey>": return <id>;`.
   Leave the old `case` line as history. The new key is new: never reuse the old
   KEY, because retired code still reads `get_level( "<oldkey>" )` and must keep
   reading 0.
2. **Lua rows.** In `tod_upgrade.lua`, REPLACE (never add beside) the old
   `DOMAIN[<id>]`, `DETAIL[<id>]` and `DARK[<id>]` rows. A Lua table with a
   duplicated key silently keeps the LAST one.
3. **Card art.** Leave `CARD_SLUG[<id>]` absent. The old slug is the OLD card's
   picture, and without a slug the card draws as text. Add a new slug only
   when the new card art is zoned.
4. **Pause plate.** Add `[<id>] = true` to `CoD.TodTextPlate` (in
   `tod_upgrade.lua`) when the id is at or below the plate ceiling (63,
   `PAUSE_PLATE_MAX`); the
   old plate names the old card, or is unzoned and draws a white square. Remove
   the entry the same commit a new plate `i_tod_pause_r<id>` is zoned.
5. **Every other id-keyed table.** Search `ui/` for `[<id>]` and `== <id>`, then
   fix each hit for the new card. Known ones: `DARK_NONE` / `DARK_TEXT_ONLY` /
   `CARD_ONE_IMAGE` / `art.icons` in `tod_upgrade.lua`, and `DARK_PLATE_NONE`.
6. **Gates.** Run `node tools/lint_tod_assets.js`. It FAILS the build on a
   reused id with a leftover `CARD_SLUG`, a reused id missing from
   `TodTextPlate`, two LIVE keys on one id, and any live card whose
   `add_domain` name differs from its `DOMAIN[id].name`.
7. **Claim it** in the table above.
