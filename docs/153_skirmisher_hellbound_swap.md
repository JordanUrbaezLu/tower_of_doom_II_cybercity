# Skirmisher ladder from Hellbound: Saug -> M1927 -> C.A.R.

> September 24 update: Skirmisher now ends with R-99; Warrior and Archer
> migrations are wired for the user playtest. Current roster, balance limits,
> build status, and asset scope: [docs/165](165_expected_roster_playtest.md).
> The C.A.R. details below describe the September 20 build.

Requested September 20, 2026. Tower of Doom II takes its class weapons from
the Hellbound sequel (`../tower_of_doom_II_hellbound`), class by class:

| Hellbound | this map | ladder | status |
|---|---|---|---|
| Skirmisher | Skirmisher | Saug -> M1927 -> C.A.R. | **this record — built** |
| Warrior | Warrior (internal slasher) | Gold Twin Knives -> Gold Sword -> Gold Battle Sword | wired, docs/165 |
| Archer | Archer (internal assault) | Bow -> R1 Shadowhunter -> Fire Bow | wired, docs/165 |
| Breacher | Heavy (now BREACHER) | Mozambique -> Remington 870 MCS -> Peacekeeper (Apex ends, user 2026-09-23) | built, docs/157 |

One class per build, per the map's hard rule (`_tod_classes.gsc:30`): the
Skirmisher is the first because it is the only mechanically identical swap
(SMG for SMG, same axes, same twin pipeline). Cards and art are knowingly
placeholders for now (user: "I know cards wont be exactly correct").

## Balance contract

User: "We can keep the DPS the same to not impact the balancing. If GDT
changes are needed to keep DPS the same for the migration lets do it."

Same mechanism as the MSMC swap (docs/139): the retired gun's emitted numbers
become the new gun's `dpsReference`, so damage is re-derived at the port's own
fire interval and DPS is unchanged. Tiers two and three then fall out of the
generator's `TIER_DPS` at their own rates exactly as the MP5 and MP7 did.
Magazines and reserve counts are pinned to the retired guns' emitted values so
the never-shrink clip floor does not reshape the class.

| Tier | Gun (source asset) | Base damage / interval | Packed damage / interval | Mag base / packed | Retired gun it matches |
|---|---|---|---|---|---|
| 1 | Saug (`hb_saug`) | 173 / 0.066 s | 218 / 0.0528 s | 32 / 40 | MSMC 210 / 0.080, 264 / 0.064 |
| 2 | M1927 (`t8_m1927`) | 263 / 0.064 s | 329 / 0.0512 s | 35 / 44 | MP5 288 / 0.070, 360 / 0.056 |
| 3 | C.A.R. (`hb_car_d0`) | 413 / 0.0645 s | 516 / 0.0516 s | 40 / 50 | MP7 411 / 0.064, 514 / 0.0512 |

DPS deltas: Saug 0.14% / 0.09%, M1927 0.12% / 0.03%, C.A.R. 0.30% / 0.39%
(integer rounding at each gun's own rate). 11 reserve magazines on all three.

Two deliberate GDT deviations from the Hellbound sources, both balance:

- **C.A.R. falloff.** The Apex port ships minDamage 20 on damage 100; the MP7
  it replaces was 358 on 411 (0.871). `tune.set.minDamage 87` pins the ratio,
  so the emitted 360 / 450 hold the MP7's ranged damage. Without this the gun
  kept the MP7's DPS up close and lost 80% at range.
- **Saug PaP optic removed.** Hellbound's Stellar 92 carries a `vm_t8_elo`
  sight; this map's rule is no dots on packed forms (user 2026-09-15), so the
  `_up` form gets `noOptic()` with the base iron-sight ADS anims.

Kept from the MP7: `axisMaxUp h:4` (the dark HANDLING rung on the packed T3
form) and `penetrateType medium` (the "T3 must not be a penetration
downgrade" rule; all three Hellbound SMGs ship small).

## Naming: `cc_*` stems

Both repos deploy into ONE Mod Tools root, and Hellbound's `hb_handling.gdt`
already emits `hb_saug_h0..h6`, `t8_m1927_h0..h6`, `hb_car_d0h0..` — the same
suffix shape this generator produces. Emitting under the source names would
double every asset in gdtdb. So the forms are `cc_saug`, `cc_m1927`, `cc_car`
(+ `_up`, + the `_f?h?` / `_h?` ladders); `srcAsset` is the Hellbound block,
`name` is ours, and nothing in the map spells the source names.

Registration ledger unchanged: 32 + 8 + 9 = 49 forms, 207 generated + 26
fixed = 233 (guard 235). Weapon-cost table 234 / 240 (the retired MSMC / MP5 /
MP7 rows are now swept by the generator's retired-stem list). The hand-zoned
`t9_mp5` / `t9_mp5_up` source lines are gone.

## Sources and the cross-repo dependency

- `donor_gdt/hellbound/hb_saug.gdt`, `hb_car_progression.gdt` — snapshots of
  the Hellbound GDTs, read by the generator, deliberately OUTSIDE
  `source_data/` so the sync never installs a second copy (see
  `donor_gdt/README.md`). The M1927 reads `skye_t8_m1927.gdt` from the tools
  root like every other Skye port.
- The clones still reference Hellbound's xmodel / xanim / material / image
  entries (`hb_saug_view`, `hb_car_base_view_sight`, `hb_am_car_*`,
  `hb_am_car_vm_apex_r97_*`), which live in `hb_saug.gdt`,
  `hb_car_progression.gdt`, `hb_car_base_*.gdt` and `hb_apex_mythic_*.gdt`
  at the tools root, installed there by the Hellbound repo's sync. The
  generator's `hbPreflight()` throws if any of those seven files is missing.
  A fresh machine needs one Hellbound build before this map links.

## Sound

Saug and M1927 are two-wav ports: their 17 alias rows are copied verbatim
from Hellbound's `hb_ports.csv` into `sound/aliases/tod_ports.csv`, and the 13
wavs are vendored under `sound_assets/skye_ports/t8_saug9mm/` and
`t8_m1927/` (the same tools-root paths Hellbound uses, byte-identical). The
C.A.R. fires through Hellbound's looping `hb_am_car_fire_plr/npc` aliases
(start / loop / tail under `sound_assets/hb/apex_mythics/`), two rows copied
from `hb_apex_mythics.csv`. The 16 MSMC / MP5 / MP7 alias rows are removed
and `t9_mp5` is disabled in `gen_tod_sounds.js`; their wavs stay on disk.

## Everything that moved together

- `tools/gen_tod_twins.js` — LADDER.skirmisher (three entries), `HB()` +
  `hbPreflight()`, retired stems in the CSV sweep
- `scripts/zm/zm_tower_of_doom/_tod_classes.gsc` — three `register_gun` lines
- `scripts/zm/zm_tower_of_doom/_tod_upgrades.gsc` — `set_guns` firerate /
  adrenaline / secondwind
- `zone_source/zm_tower_of_doom.zone` — t9_mp5 lines retired
- generated: `source_data/tod_weapon_twins.gdt`, `zone_source/tod_twins.zpkg`,
  `gamedata/weapons/zm/zm_levelcommon_weapons.csv`
- `ui/.../AetheriumLoadout.lua` — `cc_*` stems and the six display names ride
  the old mac10 / mp5 / mp7 icon cells until art is drawn
- `ui/uieditor/menus/hud/tod_class_select.lua`, `tod_upgrade.lua` — fallback
  text ("SAUG > M1927 > C.A.R.", "Saug only", "M1927 only", "C.A.R.,
  Pack-a-Punched")
- `docs/armory.html` — class guns, GUN_NAME, three gun bindings, GUNS rows,
  reload table
- `tools/test_starter_weapons.js` — guards the Saug pin, the M1927 / C.A.R.
  DPS hold, the C.A.R. falloff ratio, the optic removal and 33 alias rows

Gates passed: weapon/PaP lint (15 guns, 182 requested names), weapon costs,
starter test, arity, Lua, assets, armory constants / domains / render, sound
context, hints, damage guard.

## Known placeholders

- Class card art and gun HUD icons still show the MSMC / MP5 / MP7 pictures.
- PaP camo: the Saug (BO6 mesh) and C.A.R. carry no weaponcamotable, so the
  tier camos will not render on them; the M1927 has Skye's table.
- The C.A.R.'s damage ranges (`maxDamageRange` / `minDamageRange`) are the
  port's; only the min / max damage ratio was pinned.

## Build

`-GscOnly` BUILD OK 2026-09-20 (third attempt: the first failed the staff
manifest's pinned twin block count, 247 -> 243, updated; the second died on a
transient `Missing source checksum` for a stock footstep wav, rerun per
CLAUDE.md). FF 179,327,872 bytes, sound bank 197.9 MB (full). The linked
asset list carries 311 `cc_*` rows and zero `t6_msmc` / `t9_mp5` / `t6_mp7`
rows; the xmodel ledger carries `hb_saug_view`, `hb_car_base_view_sight` and
`hb_am_car_world`. No new linker errors beyond the ten waived ones. The
`gdtdb /update exited 1` warning predates this change (it is in the seed
build's log too). UNPLAYED: the user tests; look for `[TOD_STARTER] REGISTER`
in console_mp.log and the class picker's SAUG line.
