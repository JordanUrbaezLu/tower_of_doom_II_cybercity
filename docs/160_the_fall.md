# 160 — THE FALL: Tower of Doom II starts at the top

*2026-09-23. Built, unplayed. The user tests.*

## 1. The ask

> "All the players will spawn up in the crown room, and players will get
> overrun and ... it's going to be about $5,000 to open up the gate ... it's
> really supposed to build anxiety and players just really want to get out of
> there because they're going to die, and once everyone's out of the crown the
> doors will lock up ... they actually need to go down instead of up. And the
> map is going to be called Tower of Doom II Fallen Cybercity ... zombies kind
> of come in sprinting right off the bat, and then once that door is open and
> everyone's past that door that door locks up and the game actually slows
> down and it really starts then."

> "Similar to Moon, I do want to clean out the crown so there's no ammo crates
> or anything. What I do want to add is a pack-a-punch. So that for highly
> skilled players, they can kind of stay there, rack up some money and then
> pack a punch and then they can leave."

The Undercity, the plaza and the four workshop wings (docs/158) stay exactly
where they are; they are the run's END now instead of its start.

## 2. The route

```
CROWN HALL (spawn, crown_zone)  ── the Fall gate, 5000 ──►  THE CAUSEWAY (7360 u of road)
   Pack-a-Punch only                (seals behind the party)          │
                                                                      ▼
                                                        THE TERRACE (Quick Revive)
                                                                      │  roof door, 750
                                                                      ▼
                                              floor 50 ─► 49 ─► … ─► 1  (enter_lapN opens DOWN)
                                              lounges 40 / 30 / 20 / 10 on the way
                                                                      │  enter_lap1, 3000
                                                                      ▼
                                                THE PLAZA ─► workshop wings, the power hall, the bay
                                                                      │  enter_base, 750
                                                                      ▼
                                                THE SHAFT ─► THE CONDUIT ─► THE VAULT (the bottom)
```

## 3. The crown phase

| thing | what | where |
|---|---|---|
| spawn | 8 points in the nave's north bay, facing the gate | `gen_tower_map.js` HALL_SPAWN_*; `info_player_start` + the `start_room` group, plus a `crown_zone` respawn group |
| zone | the hall is `crown_zone`, the START zone; the road/terrace/stair stay `roof_zone` | ZONES; `zm_tod2_cybercity.gsc` init_zones + `add_adjacent_zone( crown_zone, roof_zone, tod_fall )` |
| sprint | every zombie at full sprint while `level.tod_fall_phase` | `_tod_zombie_speed::rate_for_round` (never below 1.0, never above the round curve) |
| trickle | spawn delay × 0.7 while the phase holds (round-granular) | `_tod_endless_rounds` TOD_FALL_SPAWN_MULT |
| power | ON from the first frame (turn_power_on_and_open_doors + perk_unpause_all_perks) | `_tod_fall::power_on` |
| the hall | Pack-a-Punch (east shrine, already there) and nothing else: crate retired, altar retired, extraction pad light not spawned | `_tod_ammo_crate`, `_tod_upgrades::station_spawn`, `_tod_finale::spawn_props`; generator CROWN_CLEAN |
| rounds | keep advancing (THE TWIST untouched) — the longer you farm, the harder the descent starts | — |
| the gate | a row of the generated DOORS table: flag `tod_fall`, dest "the Causeway", 5000 party-scaled, no anti-vault clip (the lintel is solid) | `gen_tower_map.js` DOORS; `_tod_doors` owns the buy |

## 4. The seal (`_tod_fall.gsc`)

1. `tod_fall` flag sets (the buy). `[TOD_FALL] OPEN`.
2. Poll every 0.25 s: every LIVING player (last stand counts, spectators do
   not) must be outside `in_hall` — the doorway counts as inside, a downed
   teammate inside holds it open.
3. Hall empty for TOD_FALL_SEAL_GRACE (2 s) and nobody's origin inside the
   slab's box + 24 hull → `seal()`:
   * slab Show + Solid + DisconnectPaths (the spire hall-gate contract)
   * `level.tod_fall_phase = false` — the speed sweep re-asserts the round
     curve within 1.5 s; the trickle returns on the next rollover
   * `level.zones["crown_zone"].is_spawning_allowed = false` — the field
     stock's spawner reads per zone; `is_enabled` is left sticky
   * the hall's respawn group re-locked (`spawn_points[i].locked`, the field
     stock's selector reads) — nobody respawns behind the gate
   * every ordinary zombie still inside is deleted (elites relocate
     themselves through tod_boss_stuck_watch)
   * derez + heavy-door cue at the gate, one `IPrintLnBold`, `tod_fall_sealed`
     notify, `[TOD_FALL] SEAL round= open_for_ms= respawns_locked= zombies_deleted=`

`TOD_FALL_LOG 1` prints without the dev flag for the first playtests — zero
it before a publish.

## 5. What the descent flipped (every one a define, LOCKSTEP with `DESCENT` in the generator)

| system | climb | descent | switch |
|---|---|---|---|
| door destinations | enter_lapN → "Floor N", roof → "the Crown" | enter_lapN → "Floor N-1", enter_lap1 → "the Ground Floor", roof → "Floor 50" | `DESCENT` (generator) |
| door prices | 750 +60/lap cap 3000 from lap 1; roof 7500 | roof 750, enter_lap50 810 … enter_lap1 3000 (same ladder, met in order); the Fall gate 5000 | `descentCost(k)` |
| elite unlock ladder | enter_lap10/20/30/40 → protector/reaver/sprinter/hound | enter_lap41/31/21/11 (the door INTO each lounge from above), same order | `TOD_DOORS_DESCENT` (`_tod_doors`) |
| elite frontier | no elite ABOVE the lowest unbought door | no elite BELOW the highest unbought door | `TOD_BOSS_DESCENT` (`_tod_bosses`) |
| class tier gate | floors climbed ≥ 10 / 30 (high-water) | floors DESCENDED ≥ 10 / 30 (low-water) — shown as floor 40 / 20 | `TOD_GAUGE_DESCENT` (`_tod_gauge::tier_progress`, `tier_floor_display`); `TIER_DESCENT` in `tod_upgrade.lua` (badge art OFF — the strips bake "FLOOR 10/30") |
| music bands | high-water latch | low-water latch — the climb's order in reverse (eclipse first) | `TOD_MUSIC_DESCENT` (`_tod_atmosphere`) |
| Quick Revive pin | the Vault | the terrace (N rail, west of the mouth) | `TERRACE_QR` → `_tod_breather_data::terrace_qr_*` |
| breather DOWN pads | power only | locked on `enter_lap1` (the base is the last zone to open; a rider in a disabled zone is the Samantha drain) | `TOD_TP_DOWN_FLAG` (`_tod_teleport`) |
| the finale | uplink on the terrace, terrace gate sealed until EXTRACTION | PARKED: props spawn, terrace gate opens at init, no uplink / extraction / crown-door control | `TOD_FINALE_PARKED` (`_tod_finale`) |
| map name | Tower of Doom: Cybercity | Tower of Doom II: Fallen Cybercity | `AetheriumHud.lua` |

## 6. Decisions the user may want to reverse

* **Power is on from the first frame.** The crown PaP (CW pack) and every
  perk wait on `power_on`; the switch is at the bottom of a 50-floor
  descent. A switch on the terrace would be a free ritual thirty seconds
  after the gate; a power-free crown PaP would need a per-machine exemption
  in the vendored cwpap. The plaza's power hall, door, decals and switch are
  untouched — the switch prompts and flips nothing new.
* **Rounds advance in the crown.** Not Moon's frozen No Man's Land: with
  THE TWIST the round counter climbs while the party farms, so a Panzer can
  land in the hall at round 5. That is the anxiety as asked; freezing the
  round is a `_tod_endless_rounds` change if wanted.
* **The gate price is party-scaled** like every door (`door_cost_mult`, quad
  ≈ ×2.36). "About $5,000" is the solo figure.
* **The ending is undesigned.** The finale is parked whole (recipe intact);
  the Endless Spire's choice never fires. The Vault is a dead end with Quick
  Revive's old pad empty.
* **The partner parts** still lie beside the Vault spawn (the peer's
  placement, docs/159) — at the BOTTOM now, after the benches. Their move is
  the partner session's call.
* **The sky sign** still reads "TOWER OF DOOM II / CYBERCITY"; the darker,
  broken tower is the next art pass (a sky re-render is a full build).

## 7. Verify (logs, not a launch)

* `[TOD_FALL] INIT` / `POWER` at the blackscreen, `OPEN` at the buy, `EMPTY`
  then `SEAL` with `zombies_deleted` after the last player leaves; no `EMPTY
  aborted` spam while someone stands in the doorway.
* Zombies sprint from round 1 in the hall; the first sweep after `SEAL`
  slows them (round 5 ≈ 0.85×).
* The Pack-a-Punch prompts in the hall from the first seconds (power on).
* The Fall gate prompt: "Open Door to the Causeway [Cost: 5000]" from inside;
  after the seal no prompt, the slab visible, zombies do not path through it.
* Quick Revive stands on the terrace's north rail, west of the road's mouth.
* The roof door reads "Open Door to the Spiral - Floor 50 [Cost: 750]".
* Tier toast: "CLASS TIER 2 UNLOCKS AT FLOOR 40" once the class gun is packed.

## 9. THE HUNTERS — the Doppelghast (added 2026-09-24)

> "In this room after some time if players dont leave after 1:30 dopplghast
> will start to spawn in every 30 seconds."

**The clock** (`_tod_fall::hunters_watch`): unpaused seconds from the moment
the class draft ends. At 90 s the first Doppelghast comes up on the hall riser
farthest from the nearest player; then one every 30 s while any living player
is still inside the hall; never more than 4 alive. A card pause stops the
clock. The seal ends it; a hunter that followed the party out keeps hunting,
one left inside is deleted with the hall's zombies. Defines
`TOD_FALL_HUNT_AFTER_SECS / _EVERY_SECS / _MAX / _HP_ZOMBIES` (90 / 30 / 4 / 8).

**The actor** (`_tod_doppelghast.gsc`) is Hellbound's BO6 ghoul port
(`tower_of_doom_II_hellbound/scripts/.../_tod_bo6_dev.gsc`, docs there:
BO6_DEV_SPAWN_TEST, BO6_ENEMY_AUDIO, 111), cut to the elite lane:
`spawner_hb_doppelghast_dev` (aitype + character in `hb_bo6_dev_ai.gdt`,
model + nine converted clips in `hb_doppelghast.gdt` — both INSTALLED AT THE
TOOLS ROOT, snapshotted in `donor_gdt/hellbound/`, never in `source_data/`),
the two AI tables in `animtables/` (a new sync mapping), the two juke clips'
root-motion paths (`_tod_doppelghast_motion.gsh`), chase with a 1.5 playback
walk rate, sprint bursts, capsule-checked jukes, the 35-damage melee at frame
18, the 3 s delayed gore burst (25 splash within 128 u, LOS), and the BO6
source audio (`_tod_bo6_audio.gsc` + its generated notetrack table; the 12
alias families the code fires as `sound/aliases/hb_bo6_ghoul.csv`, 62 rows /
62 wavs / 11 MB — Hellbound's "loud on purpose" mix, DistMax 3000-3800).
HP = 8 zombies of the round's health at the party table
(`tod_zombie_speed::health_mult`), floor 500. Death = THIS map's elite lane:
`tod_luck::boss_kill` (luck + the kill confirm), `grant_elite_reward` (the
killer's 500 x2x x BOUNTY, the bottle roll), then the burst and a delete at 7 s.
The spawn tell is the hound entrance (ground lightning 1.2 s, bolt, quake).
Stuck 12 s -> a hall riser while the crown phase holds, else a navmesh point
200-600 u round the target.

**Gate:** `tools/test_doppelghast.js` runs in every build — tools-root GDTs,
xmodel/xanim bins, AI tables, zone lines, every scripted `%anim` in the
`.ai_am` (the generic-tree trap), every fired alias + its Secondary + wav, the
szc entry, the Fall wiring.

**Logs:** `[TOD_FALL] HUNT clock started / spawn / skipped / over`,
`[TOD_DOPPEL] SPAWN / READY / MELEE / DEATH / RELOCATE / DENIED` (with dev
OFF while `TOD_DOPPEL_LOG` is 1). Juke / sprint chatter is dev-only.

**Not ported:** the Amalgam, the 1.5x red boss clone, Hellbound's class-path
stuns/EMP slow, needles / hallucination / slow (never ported there either).

## 10. THE CALM, THE ALARM, THE ALTAR (added 2026-09-24, second pass)

User, the morning after the hunters: *"players pick their class and then can
walk around for 20 seconds and then there is a spinning alarm at the top of the
crown that starts a siren and this is when the flood comes in. Zombies will move
at max sprint for default max sprint in bo3. Pap will be here and the alter will
be here as well. We will change the alter model later but we can reuse for now.
Also it should be quite dark which I believe this map is."*

### 10.1 The timeline now

| Beat | What happens | Owner |
|---|---|---|
| blackscreen | power on (unchanged) | `_tod_fall::power_on` |
| the draft | the class panel, world frozen (unchanged) | `_tod_class_select` |
| the round-1 deal | still frozen (unchanged) | `_tod_upgrades` |
| **THE CALM** | `TOD_FALL_CALM_SECS` (20) of **unpaused** quiet. Nothing spawns: stock's own spawner gate, the `spawn_zombies` flag that `_zm::round_spawning` waits on before every spawn, is held clear from init. Players walk, read the room, buy nothing they cannot afford. The round cannot advance (THE TWIST waits for the round's zombies to spawn). | `_tod_fall::flood_hold / calm_watch` |
| **THE FLOOD** | the alarm beacon lights and spins, the siren wails `TOD_FALL_SIREN_SECS` (20), the flag is set, the horde rises at **exactly 1.0**: BO3's own full sprint (`rate_for_round` pins the rate while the crown phase holds; it clamped to "at least 1.0" before, which let a long farm outrun it) | `_tod_fall::flood`, `_tod_zombie_speed` |
| the hunters | the Doppelghast clock now starts **at the flood**, not at the draft: 1:30 after the siren, then every 30 s (the calm threatens nobody, so it is not counted). One define (`TOD_FALL_HUNT_AFTER_SECS`) if the user wants the clock from the draft instead. | `_tod_fall::hunters_watch` |
| the gate, the seal | unchanged, with one addition: the seal is **island-aware** (see 10.4) and brings the beacon and siren down | `_tod_fall::seal` |

### 10.2 The alarm

- **Housing** (generator section 5d'): a gold gantry spanning the hall at the
  wall tops on the dais axis (y = HYC, x −728..728, z +544..+568), a pendant,
  and a **red core** (48 cube, z +456..+504) hanging over the hall's centre.
  Plain hues on purpose: the `_tinted` brass and the `_tinted_edge` ruby are
  DECK-class to `lint_tod_geometry`, and a deck under 64 thick reads as a
  floor (158 unguarded edges on the first lint; the peer session caught it).
  Anchor: `tod_crown_data::alarm_org()`; orbit radius `alarm_orbit_r()` (96).
  Nothing rotates in the map: a grep of every stock prefab found **no brush
  entity with a pivot key**, so a spinning `script_brushmodel` is an untested
  lane and was not used.
- **The spin** (`_tod_fall::alarm_start`): a `tag_origin` script_model at the
  core turns one revolution per `TOD_FALL_ORBIT_SECS` (1.5); two more hosts
  `LinkTo`'d to it at the orbit radius circle it. Each host wears a
  **todPerkGlow** value, the clientfield + client `PlayFXOnTag` lane this map
  has rendered since map 1: the core takes **index 11**, new, =
  `light/fx_light_flashing_red_factory_zmb` (the Giant's 1 Hz red alarm light,
  the effect Map One's DEFCON lockdown drove on the same lane); the orbiters
  take **index 1** (the red perk aura). The hall flashes red and two red glows
  sweep round the core. Zone line + client precache added in
  `_tod_perk_lights.csc`.
- **The siren**: `tod_fall_siren`, a **LOOPING 3D** row in `tod_bosses.csv` on
  the stock Civil Protector police siren (`zmb\ai\civil_protector\police_box_siren.wav`,
  5.1 s, already in every zm bank; vol 90, 600 → 3000/3600). Played with
  `PlayLoopSound` on a `script_origin` at the core; stopped with
  `_tod_atmosphere`'s three-call recipe after 20 s, or at the seal.
- At the seal: glows to 0 first (the client `StopFX` runs on the field
  change), a snapshot later the hosts are deleted.

### 10.3 The altar is back

`_tod_upgrades::station_spawn` places the crown terminal again (id 5, west
shrine, the same anchors, the same 3-use cap). The heavenly-altar mesh is the
placeholder: *"we will change the alter model later"*. The crate stays retired.

### 10.4 The island seal (docs/163, a peer session, same day)

A concurrent session is cutting the causeway to two stubs with a one-way
**jump pad** between them; the hall plus its stub become an island and
"everyone is out" becomes "everyone has crossed". GENERATED crown data now
carries `jumppad_enabled()` and `on_crown_island()`; `_tod_fall::in_sealed_area`
reads them (`jumppad_enabled() ? on_crown_island() : in_hall()`) for both the
seal count and the zombie sweep at the seal, so a player left on the crown's
stub can never be sealed off, and a body on the stub is deleted like one in the
hall. Two more rules from the peer's findings: a player **mid-flight** on the
pad (`p.tod_jumppad_flying`, ~4.5 s outside every zone volume) counts as still
inside, and after the seal `hall_spawn_guard` re-asserts
`crown_zone.is_spawning_allowed = false` every 0.5 s, because stock's
empty-spawner failsafe (`_zm_zonemgr::manage_zones`, "Special logic for empty
spawner list") sticks the INITIAL zone back on whenever nobody occupies any
zone. The hunters still target players **in the hall**. The crown's stub is a
second brush of `crown_zone`, so `TOD_FALL_ZONE` already covers the island.

### 10.5 "It should be quite dark" — what this pass did about lighting

The user's belief is not what the data says (docs/162 README, "Tower of Doom
II today"): all 344 lights are on from spawn, every visible face is emissive,
the sky throws ~5.6 stops more light than a stock night, and the state the
game runs in had **no SSI of its own** (the linker filled it with
`default_day`: a daytime sun at stops 14 and an exposure clamp of 1..16). This
build carries docs/162's **Step 0 and Step 1**, three generator switches, all
ON: `LIGHT_TEST_T1` (a GREEN light lit only in Radiant State 1 and a RED one
only in State 2, on the hall's west wall level with the spawn, plus the
`[TOD_LIGHTSTATE]` log), `SUN_SSI2` (`ssi2` = the night SSI), and
`SUN_PROBE_TARGET` (the global probe targeted at an `info_null` in open air
over the plaza ring at (490, −120, 200), asserted outside every box). Read
docs/162 10 §7.3 for what each screenshot means. The crown hall's own lights,
its gold, and the sky are untouched in this build: they are the next levers,
and the user decides them (docs/162 README "Recommended plan", steps 2–7).

**Superseded the same afternoon by docs/164 (THE DARK PASS, part one):** the
user answered the four questions (near-black with pools / edge lines only /
darken the sky / crown hall first) and that pass moved the levers this section
only named — the hall's faces, its lights and the sky. Read docs/164 for the
current hall lighting; this section is the record of the test build before it.

### 10.6 Verify (logs, not a launch)

- `[TOD_FALL] HOLD` before the blackscreen, `CALM` at the end of the draft,
  `FLOOD` ~20 unpaused seconds after the deal (check `round=1`), `ALARM up`,
  `SIREN on` … `SIREN off` 20 s later, `HUNT clock started at the flood`,
  `SEAL … zombies_deleted=N`, `ALARM down`.
- `[TOD_LIGHTSTATE] at=blackscreen|power_on|spawned … level=1 player=1`
  expected; anything else is news (docs/162 T1).
- In the hall: 20 quiet seconds after the cards, then a red flashing light
  overhead with two red glows circling, a siren for 20 s, zombies at full
  sprint; the altar on the west wall, the PaP on the east; the green/red test
  lights on the west wall by the spawn.

### 10.7 Decisions the user may want to reverse

- the calm is 20 s of **unpaused** time after the deal (not after the draft);
- the siren stops after 20 s while the beacon keeps spinning to the seal;
- the hunters' 1:30 counts from the siren, not the draft;
- the three lighting switches are ON together (one build answers all three;
  flip one OFF to bisect if the look moves in a way nobody expected).

### 10.8 THE LEVER, THE INTRO, THE NUCLEAR SIREN (2026-09-24, late evening)

The timed calm is gone (kept behind `TOD_FALL_LEVER 0`). The sequence now:

1. **Spawn.** The intro track (`tod_fall_intro`, the user's "Deep Mystery",
   30.2 s) plays once from the blackscreen. No band music in the hall.
2. **The lever.** The stock power switch (body + handle, script-spawned) stands
   on the sanctuary's top step in front of the reredos, facing the hall; the
   prompt says "activate the power" and shows once the draft is done. Nothing
   spawns until it is pulled - rounds sit at 1.
3. **The pull.** The handle flips with stock's own sound, sparks and the
   turn-on sound. If the intro is still playing it is cut in that same tenth of
   a second, before the flip finishes. The beacon spins and the nuclear siren
   (30 s, `tod_fall_siren`) winds up at once.
4. **The flood.** Ten seconds after the pull (`TOD_FALL_LEVER_LEAD_SECS`) the
   spawns release; the Doppelghast clock counts from the pull, as before from
   the siren. The seal, the descent and the bands are unchanged: the bands start
   when the crown seals.

Knobs, one line each: `TOD_FALL_LEVER_LEAD_SECS` (the wind-up), the alias
volumes (siren 90 in tod_bosses.csv, intro 95 in tod_ui.csv), `lever_org()`'s
`LEVER_Y = RER_Y1 - 32` in the generator's crown-data block (move it along the
step; the asserts hold it off the pad and the reredos), `TOD_MUSIC_INTRO 0` for
the old band-at-spawn behaviour. Logs: `[TOD_FALL] LEVER spawned / armed /
pulled by <name>`, `FLOOD ... spawns in 10 s`, `RELEASE`, `SIREN on/off`;
`[TOD_MUSIC] INTRO up ... / CUT by the lever / ended`.

Build: -GscOnly BUILD OK 2026-09-24 23:27:05 Eastern, FF 198,784,448 B; diffs
clean, nothing synced after, the switch models and the sparks fx in the ledger,
both wavs deployed byte-identical. UNPLAYED.

**THE VEIL (2026-09-25, after the lever):** the user wants the map fogged until
the power is on and the detailed sky revealed when it is, by shifting the fog
rather than deleting it ("it breaks sometimes"). `_tod_atmosphere.gsc`
`TOD_VEIL 1`: while the calm holds the tower sits in an even ash haze
(halfdist 520, no altitude falloff, 0.22/0.20/0.26) written through the same
change-gated `set_fog` the spire's fog uses; the sky is hidden because the fog
asset fogs the skybox at 65,000 units, so at that density the sky is the veil's
colour. From the lever pull `tower_fog()` lerps the halfway distance out on a
cubic ease over 12 s to 60,000 and then falls back to the exact `fog_off()`
state every previous build ran - a shift, never a kill. Knobs: `TOD_VEIL_*`.
Log `[TOD_VEIL] UP / CLEARING / CLEAR`, once per state. Coded and gated; the
build was blocked by a peer's Archer GDT - see the CHANGELOG entry. The peer's
00:34:52 full build (docs/169) carries the lever, the intro and the siren but
NOT the veil (its sync preceded this edit).

### 10.9 THE BALCONY, THE OVERLOOK, THE LEVER IS THE POWER (2026-09-25)

The user's brief: the balcony must fit an empty shop, the jump pad and Quick
Revive; the power switch goes in another room off it where players can look
down the tower, so that pulling it shows them the tower lighting up, the fog
lifting and the sky; "a few rooms behind doors"; nothing that needs power (the
jump pad, Quick Revive) works before it.

**The plan.** Out of the hall gate (open from the start now), through the
crown's mouth, onto THE BALCONY: 1280 wide, 640 deep, rails all round. The jump
pad sits 240 in from its south rail on the centreline; the display shop stands
on the west half facing the pad (a fourth item shop that the cycle never
activates: dark and silent by construction); Quick Revive backs the north rail
west of the mouth. Off the EAST rail a 160-wide passage leads to a 480 x 380
antechamber, and south of that THE OVERLOOK, 480 x 400, hanging over the void
with its south rail facing the tower. The lever stands at that rail, front to
the room: a player pulling it faces the drop, the tower and the sky. Every
piece is a road cell, so the rails, the zone box and the sealed-island test
follow from the geometry.

**The power.** Pulling the lever calls stock's own power-on. Everything that
already waited on the power flag now waits for the lever: perks (solo Quick
Revive is stock's exception and sells from round 1), the crown Pack-a-Punch,
the teleporters, the item shops, and the jump pad, which refuses with
"no_power" until then. The fog veil (§10.8's addendum) and the siren also key
on the pull. The hall gate is opened free at init because a paid door before
the first zombie can never be bought; the seal still closes it behind the
party. The doorways between the balcony, the antechamber and the overlook are
cut as openings: door slabs can be added once a pre-power money source exists.

**Knobs.** `JP_LAUNCH_HALF` (balcony width), `OV_*` cells (rooms), `OV_LEVER`,
`TERRACE_QR`, `CROWN_SHOPS[3]`, the `AVENUE` pylon pairs, the five `HL` pools.

**Not in this pass.** Tower lights that come on with the power (lighting
states, docs/162 ch.02); door slabs before the lever; a bigger lever model.

**Build record.** (appended below by the build that carries this pass)

**FULL BUILD OK 2026-09-25 01:49:25 Eastern.** FF 206,961,984 B; fresh BSP
(01:46:07) + LED 100,176,498 B (01:47:47); navmesh 3 components (tower, spire,
the crown island: hall + balcony + overlook + pad in one, 108 faces); banks
109,442,176 / 209,338,496 B; compiled `.map` md5-identical to the repo's regen;
scripts / zone_source / ui diffs clean; deployed `_tod_crown_data.gsc` carries
`lever_org() (1200, 5910, 19392)` and `jumppad_launch_org() (0, 6480, 19392)`;
deployed `_tod_fall` / `_tod_jumppad` / `_tod_atmosphere` carry the gate-open,
no-power and veil code. Nothing synced after the `.ff`. (The peer session's `_tod_archer.gsc` fix
landed at 01:47:47, between this build's sync and its link; a first diff read
it mid-write, a byte compare after shows repo == deployed, so this `.ff`
carries their fix too.) Log: tmp/balcony_build/build.log. UNPLAYED; the user
tests.

### 10.10 TWO SWITCHES, ONE SHOP, ONLY ZOMBIES, THE 5000 GATE (2026-09-25, after the first co-op play)

The user's notes: two item shops inside the crown, one wanted; "there should be
a switch to start the alarm, but that should be inside the crown"; "there
shouldn't be any mobs on the map except zombies right now"; the hall gate was
open and "should have been closed ... there needs to be a trigger, it should be
5,000"; zombies sprint; nothing spawns before the alarm.

**The run's opening, as built.** Spawn in the dark hall to the intro track.
THE ALARM SWITCH (the stock switch on the sanctuary's top step, in front of the
throne wall) is the game's start: the intro cuts, the red beacon spins, the
nuclear siren winds up and the zombies (sprint gait, full rate) come 10 s
later. Their points buy THE GATE (5000 solo, party-scaled like every door).
Past it, the balcony and the overlook, where THE POWER SWITCH (armed only
after the alarm) turns the grid on: perks, Pack-a-Punch, shops, teleporters,
the jump pad, and the lighting wave (docs/164 §9). The seal still closes the
gate once everyone has jumped.

**One shop.** The west bay's hut is the hall's only shop and is always the
active one (`TOD_SHOP_CYCLE 1`); the east and north copies are gone; the
balcony's display hut stays dark.

**Only zombies.** One flag, `level.tod_only_zombies`, set in the entry
script; every elite director and the Doppelghast clock stand down on it.

**Build record.** FULL BUILD OK 10:57:28 Eastern (tmp/blackout_build/build.log): FF 206,779,392 B, fresh BSP + LED 100,173,570 B, navmesh 3 components, 8 known-waived warnings (none a tod_black_*), all 24 tod_black_* materials the map uses in the linker ledger, banks 109.4 / 209.3 MB. It carries everything in this pass EXCEPT the 5000 gate (TOD_FALL_GATE_OPEN 0, edited after its sync): the -GscOnly meant to carry it halted before the linker on a PEER session's in-progress tools/art_cohesion/verify_surfaces.py (a crown-material pass that keeps world emission at zero); that crown session is a THIRD session (not the sky session). ITS OWN FULL BUILD then carried the gate: BUILD OK 11:20:25 Eastern (tmp/art_cohesion/full_build.log), FF 206,925,056 B, LED 100,170,906 B, navmesh 3 components, 8 known-waived; its sync ran after the gate edit (10:52:09), so the 11:20:25 .ff has EVERYTHING in this pass plus the crown's textured surfaces. That -GscOnly's sync did run, so the deployed SOURCE tree is newer than the .ff — the .ff itself is the 10:57 build.

### 10.11 THE SIREN LOOPS UNTIL THE GATE (2026-09-29, session fd)

User: "The Alarm does not stay on forever like it should. It stops at some point and we need it to
loop. We have tried this multiple times. Should stop once door is bought."

Two causes, both read off the user's 13:03 run (`tmp/elite_tracking/runs/20260929_130328_358_02ca098f`):

- **The door's shutdown killed itself.** `alarm_until_escape` ends on `tod_fall_alarm_off` and called
  `alarm_stop()` inline, whose FIRST line raises that notify, so the thread died before `siren_stop()`
  and the beacons' `stop()` ran: "ALARM off: the escape door opened" at ms 105450, "SIREN off" only at
  the seal. It threads `alarm_stop()` now, as the seal always did; test_doppelghast fails the old shape.
- **The one-shot outran a pause.** The 30 s siren (template UIN_MOD: Pauseable no) was re-played every
  28 s of GAME time; an ESC pause of 154 s let it finish while the timer stood still, so the hall went
  quiet until the next tick.

Now the siren is three Pauseable 3D rows in `tod_bosses.csv`, cut from the unchanged 30 s master by
`tools/fall_siren/make_siren_clips.py` (re-run it; never hand-edit the clips):

| row | clip | role |
|---|---|---|
| `tod_fall_siren_start` | 7.05 s | the wind-up; fades out over its last 0.35 s |
| `tod_fall_siren_loop` | 20.64 s, LOOPING | two whole wail cycles; loop points chosen by spectral match + sample alignment (0.98), the seam crossfaded into the audio before the start point (seam level step 0.2-0.6 dB against the recording's 0.8 dB median) |
| `tod_fall_siren_stop` | 3.2 s | the wind-down: a steady stretch read at a falling rate, level falling with it |

`siren()` plays the wind-up and at `TOD_FALL_SIREN_LOOP_AT` (6.7 s) starts the loop as the host's
ENTITY LOOP SOUND (`PlayLoopSound`, crossfading `TOD_FALL_SIREN_XFADE`); nothing times it out. At the
gate (or the seal) `alarm_stop()` darkens the beacons at once and `siren_stop()` fades the loop under
the wind-down, then deletes the host once the wind-down has played. A once-a-second guard respawns the
host and restarts the loop if anything ever deletes it while the alarm is up. LOCKSTEP: `XFADE`,
`LOOP_START` and `STOP_SECS` in the clip script vs the `TOD_FALL_SIREN_*` defines (test_doppelghast
checks all three, and the wind-up clip's length). Logs: `[TOD_FALL] SIREN on: wind-up`, `SIREN loop on`,
`SIREN still looping after N s` (every 60 s), `SIREN off: the loop fades under the wind-down`,
`ALARM off: the escape door opened`.

## 8. Build record

### 2026-09-24 12:57:45 Eastern — FULL BUILD VERIFIED BY THE FRESH .ff (the runner's log ends after the teleporter validator without the script's verdict line — that session was replaced at ~12:59 — and the two validators after it, item-shop and partner assets, could NOT be re-run here: a third session's full build started ~13:16 and its sync had already wiped the asset ledger; that newer build will REPLACE this .ff — verify it before playing) (the calm / alarm / altar pass + docs/162 T1-T3 + the peer's causeway cut)

ONE build for two sessions, run by the jump-pad session (docs/163) on the tree
as of my 12:49:56 regen (their regen reproduced the `.map` byte-identically);
log `tmp/jumppad_20260924/build.log`. Verified from this session after the
`.ff` landed:

| Check | Result |
|---|---|
| `.ff` | `zm_tod2_cybercity.ff` 211,194,688 B at 12:57:45 |
| repo vs deployed `diff -rq` scripts / zone_source / ui | clean (only the linker's `all/ english/ loc/` outputs) |
| deployed files newer than the `.ff` | none |
| assetinfo ledger | `light/fx_light_flashing_red_factory_zmb` present (fx + its lightdescription); 27 `hb_bo6_doppelghast` rows |
| sound banks | `.all.sabs` 207,523,840 B (197.9 MB, full); `.all.sabl` 63,287,040 B (+0.5 MB: the siren wav) |
| BSP / navmesh | `.d3dbsp` 12:53:40; navmesh 1131 faces, **3 components** (tower, spire, the crown island — the peer's new island check passed) |
| LED | **100,163,686 B at 12:55:26 — double the 50.5 MB of every earlier bake.** The per-state SSI table now reads `[tod_ssi_cybercity, tod_ssi_cybercity, default_day, default_day]`: `ssi2` landed (docs/162 T2), and a second filled state costs a second full probe/sun-shadow bake (docs/162 T13 answered: ~+49.7 MB LED per state). |
| deployed `_tod_fall.gsc` | `TOD_FALL_CALM_SECS 20`, `TOD_FALL_LOG 1`, `TOD_LIGHTSTATE_LOG 1` |
| lints in the build | geometry OK (citadel→terrace by the pad, one-way by design), test_jumppad OK, test_doppelghast 170 checks, 10 known-waived asset warnings only |

No launch; UNPLAYED. The user tests.

* **FULL BUILD OK 2026-09-24 00:06:11 Eastern** (the layout: geometry + LED +
  linker): FF 210,603,648 B; fresh LED 50,487,469 B; navmesh 1139 faces / 2
  components (tower + crown road, spire); bank 197.9 MB; only the 10
  known-waived asset warnings. Log `tmp/fall_20260923/build.log`.
* **-GscOnly BUILD OK 2026-09-24 00:28:07 Eastern** (the Doppelghast, the
  doors brace fix): FF 211,364,224 B; streamed bank 197.9 MB, loaded bank
  62,764,288 B (+4.6 MB = the 62 ghoul wavs); the assetinfo ledger carries
  `spawner_hb_doppelghast_dev`, `c_hb_doppelghast_dev`, `hb_bo6_doppelghast`
  + its 5 materials / 21 images, 14 `hb_doppelghast_*` xanims (11 zoned + the
  3 AI-table clones) and both blood FX (sound aliases are not ledgered: the
  loaded bank grew by the 62 ghoul wavs and the csv is deployed); the AI tables are deployed to
  `usermaps/zm_tod2_cybercity/animtables/`; `diff -rq` scripts / zone_source /
  ui clean, nothing synced after the `.ff`; only the 10 known-waived asset
  warnings. Log `tmp/fall_20260923/build_gsc.log`. The `.map` was
  byte-identical to the 00:06 build's (md5 33164a87…), so the geometry compile
  and bake of the full build stand.
* No launch. UNPLAYED — the user tests.
