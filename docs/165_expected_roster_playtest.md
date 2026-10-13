# Expected roster for the September 24 playtest

The user requested dev and god mode and the expected class guns before their
own test. This completes the Warrior and Archer migrations planned in
docs/153 and replaces the Skirmisher's C.A.R. with the R-99. The installed
converted assets are used here; the newly extracted Apex source library is
available for a later visual/audio quality pass.

| Class | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| Skirmisher | Saug | M1927 | R-99 |
| Archer | Bow | R1 Shadowhunter | Fire Bow |
| Breacher | Mozambique | Remington 870 MCS | Peacekeeper |
| Warrior | Gold Twin Knives | Gold Sword | Gold Battle Sword |
| Mage | Lightning Staff | Fire Staff | Ice Staff |

Mage remains additive. Internal class keys `assault`, `heavy`, and `slasher`
stay in place to preserve IDs, saved state, secondaries, and upgrade domains.
All secondary weapons are unchanged. Weapon clones use private `cc_*` names.

## Wiring and presentation

The generator, runtime roster, gun-specific upgrade bindings, Pack-a-Punch
CSV, generated zone include, ammo-crate exclusions, HUD identity lookup,
class labels, tier labels, and armory agree on the new stems. Gold Battle
Sword inherits Cybercity's Thor's Thunder; Gold Sword gets Draw Cut; Fire
Bow gets Forced March; R-99 gets the Skirmisher tier-three handling domains.
The dark variants remain packed-only.

Class selection and tier promotions use their existing text fallback while
the baked cards name retired guns. Small HUD icons still reuse existing
categories and need replacement art. No new high-resolution art is claimed.

Six donor GDT snapshots live in `donor_gdt/hellbound/`, outside the synced
`source_data` directory. Model, material, animation, and image dependencies
come from the donor library already installed in the private tools root.
The Fire Bow uses the corrected Rune Prison models/materials.

`tod_expected_roster.csv` adds 226 context-free rows and 164 vendored WAVs:
R-99 fire/foley, crossbow, Citadel sword sounds, Gold Sword, and the dual
katana motion sounds used by Gold Twin Knives. Stock `elemental_bow_sounds`
is included in the map sound configuration. Peacekeeper's existing audio and
quality models remain unchanged.

The completed linker reports four stock bow material diagnostics for Rune
missile/rocks and Storm crystals/orb on the base bow, and two Storm materials
on Fire Bow. The corresponding variant attachment tags are in the donor
weapon's hide list; this is not proof that every affected triangle is hidden
in game. Keep these diagnostics with the asset-quality follow-up. No warning
was added to the build's waiver list. Generic `wpn_generic_dryfire_plr/npc`
references inherited by Peacekeeper/R-99 are outside the local sound bank;
their availability in the game's common banks is not established by this
audit. Fire, reload/foley, and bow-specific sound entries are verified locally.

## Balance boundaries

R-99 retains the retired tier-three firing DPS, 40/50 rounds per magazine,
11 reserve magazines, medium penetration, and the prior falloff ratio.
Base/PaP damage is 436/545 at 0.068/0.0544 seconds. All 105 retained generated
blocks compare exactly with the pre-migration snapshot, including every
secondary, all Breacher and Mage forms, Saug, and M1927.

Warrior preserves melee damage 1600/3200/5440, doubled by PaP, and the prior
Cybercity swing timing ladder. Native lunge stays disabled. The retired bat's
hoop presentation cannot attach to these new weapons; its raw legacy asset
and isolated tests remain available.

Archer's direct-hit budget is derived from the retired rifle's GDT fire/reload
cycle. **This is a reference calculation, not measured charged-shot DPS.**
Native draw time, projectile travel, splash, and the single-bolt reload need
the user's playtest. Base direct damage: Bow 441, crossbow 2071, Fire Bow
1199; packed 644/2776/1726. Fire Bow keeps donor splash. Quivers begin full
at every mag/PaP rung, with zero reserve; crossbow starts with one bolt and
52 reserve magazines. Integer rounding means early crossbow magazine rungs
do not increase its one-bolt chamber. Existing Cybercity card domains are
retained; redesigning Archer-specific upgrades is outside this wiring pass.

Hellbound's scripted bow charge multiplier, fire burn/geyser, and Warrior
bash/smash systems were not imported. No claim that those class mechanics
are present in Cybercity.

## Playtest settings and evidence

`level.tod_dev` and `level.tod_god` are true in the entry script. The existing
dev mode grants test money and opens doors. God mode is the map's existing
damage protection (floors lethal damage at one health). Maxed loadouts,
automatic upgrade testing, and class-specific test harnesses stay off.
The old aim-moving/zombie-killing hoop probe now requires its own
`tod_dev_hoop_probe` switch, which is false.

The user launches and plays. New automatic `[TOD_ROSTER] READY`, `REGISTER`,
and `GIVE` lines report the armed settings, all class/tier bindings, resolved
weapon identity, grant success, and missing-weapon failures. Archive the
user's next `console_mp.log` with `tools/capture_ai_logs.ps1` before diagnosis.

Static validation passed: expected-roster checks (126 changed weapon forms,
all 12 non-Mage tier bindings, dark rungs, quivers, melee damage, WAV format),
starter/Breacher balance, Pack-a-Punch resolution, legacy bat behavior, GSC
arity, armory constants/domains, and sound-context lint. The full guarded
build runs the new `tools/test_expected_roster.py` gate too.

Full guarded build passed. Fresh fastfile: **199,670,080 bytes, September 24
at 22:48:46 Eastern**; LED 100,163,699 bytes; loaded/streamed sound banks
106,904,704 / 207,523,840 bytes. Post-build model checks passed. Deployment
comparison: 346 inputs, zero differences and zero inputs newer than the
fastfile; 240 expected weapon/model entries present and all 174 checked
map-local audio aliases present. 207 generated + 24 fixed weapons (guard
235), weapons-cost table 234/240. No new `ERROR:`-class linker messages;
donor bow diagnostics and inherited common-bank audio limits are recorded
above, not waived or claimed fixed.

Evidence: `docs/expected_roster_evidence/build.json`; detailed build,
source snapshot, deployment report and preserved linker transcript under
`tmp/expected_roster/`. The first attempt stopped on an existing test that
matched JSON whitespace; that check now parses the sound configuration.
The retry used `-SkipSync` because deployed runtime inputs were already
identical, and still ran every full build stage and gate. Nothing was synced
after the fastfile. No native playtest was performed by the agent.
