# 208 - The Map One migration pass (2026-10-04)

User, 2026-10-04: *"Map one made some changes to adding numbers to each floor. Lets add that
too but we go down instead of up so we should add in a spot that makes more sense as players go
down. Also check a few other things. They made a ton of updates we never migrated over. like
textures, models, etc"*

Tower II was seeded from Map One (TOD1, `tower_of_doom_cybercity`) on 2026-09-20. Map One kept
shipping: its CHANGELOG lines 1-2613 (v19.24 -> v19.72) are all after the seed. This pass read
every one of those entries against TOD II's code, ported what applies, and lists the rest.

**Map One was read only.** Nothing in its repository, its usermap or the shared Steam tools was
written. Every asset below is Map One's BUILT output copied byte for byte into this repository
(pinned by Map One's own manifests where it has one), and every tool that would write back into
Map One's tree (its Blender stages, its installers) was left behind on purpose; the README beside
each asset says how to rebuild it safely from here.

## What landed

### 1. Floor numbers, placed for the descent (Map One's v19.68t, redesigned)

**Superseded 2026-10-05 - the rail numbers below are RETIRED** (user: "The numbers on the railings
for each floor can be removed. I only want it on the door."). The floor numbers now ride only the
paid doors: every lap door and the roof door carries the number of the floor it opens onto, inside
its own slab entity (`doorNumber` in `tools/gen_tower_map.js`, 26 doors / 47 digits, added
2026-10-04). The atlas, the five materials, `make_assets.py --check` and `checkFloorNumbers()` stay
for the door digits. Never put numbers back on the rails. The rest of this section is the history.

Map One stands floor n's number on the core face LEFT of n's door, for a player CLIMBING to it.
Coming down, that face is on the far side of the door and faces away. Here every floor F carries
its number where a descending player ARRIVES on it: the inner face of the outer rail that closes
the walkway they come down, dead ahead of them through floor F+1's door (or across its broken
flight).

- even F: the SE end landing (`lap<F> SE landing para b`, its north face), read walking south;
- odd F: the NW end landing (`lap<F> NW landing para b`, its south face), read walking north.

Floor 50's number sits under the terrace, met off the crown stair; the plaza (the Ground Floor) has
none. The digits are the map's OWN HUD digits in the floor's district colour (blue / green /
orange / yellow / red), one non-colliding chalk-mesh quad per digit (no brush, collision, navmesh
or entity), 36 tall on the 39-tall rail. `tools/floor_numbers/make_assets.py` writes the atlas and
the five `tod_floornum_*` materials (`source_data/tod_floornum.gdt`); its `--check` (a build gate)
holds the generator's ink crops and district colours to the atlas. `checkFloorNumbers()` in the
generator proves every number has its rail behind it, nothing in front of it and a clear view from
the walkway. Emitted last: `TOD_FLOORNUMS=0 node tools/gen_tower_map.js` regenerates the map
without them byte for byte. The numbers are steady emissive and face into the tower; nobody sees
them before the power (the crown island is sealed until power_on).

### 2. The black-screen fog (Map One's v19.40 + v19.63)

`_tod_atmosphere::fog_off()` (written from `initial_blackscreen_passed` for the whole match while
`TOD_VEIL` is 0) passed a halfway HEIGHT of 0 and a start / halfway pair (100,000,000 /
100,000,001) that is the SAME float32. Both divide by zero in the volumetric fog maths on GPUs that
do not clamp - Map One's Workshop reports: "everything goes black ... other than shadows". The
halfway is now 200,000,000 and the height 1,000,000 (`TOD_FOG_OFF_*`); nothing is ever fogged and
the maths stays finite. `[TOD_FOG] SET` (tod_dev) logs each change.

### 3. Nikolai's props (Map One's v19.68n-v19.69b, v19.71's caps)

`tools/fan_props/verify.py` (pre-link + `--compiled-ledger` post-link) holds all of it to
`tools/fan_props/manifest.json` (26 files, 12 models, Map One's triangle counts).

- **The Ammo Box V6 on every crate** (`tod_ammo_chest`): 98 x 70 x 29.4, centred. `crateBox()`
  in the generator and `tools/haven_layout.js` (the haven crate) take its measured box; the clip
  is the case's own height (`CRATE_BOX_H` 30, was 58 - no invisible ledge above the box); the haven
  crate shifted 4 north so its south edge stays where the old crate's was. Triggers unchanged.
- **The TOWER OF DOOM / CYBERCITY sign** (`tod_cybercity_sign2` + `_off` / `_dim` twins) on the
  core's west face over the base crate - Map One's spawn wall, this map's Ground Floor: the bottom
  of the descent. Dark until power_on, then a neon start (`_tod_base_sign.gsc`, `[TOD_SIGN]`). The
  generator (`BASE_SIGN`) asserts it on the face, under lap 2's W flight and above the crate, and
  cuts its body clip plus a steep cap (`steepCap`, 74 deg, buried into the core) so nothing stands
  on it.
- **The Grid Terminal V5 is the crown's power switch** (`tod_power_terminal` + dial + five screen
  frames, replacing the stock lever on the power room's east wall). The press spins the dial and
  boots the screen through RESTART GRID; the power wave starts on the frame it reads POWER RESTORED
  (`_tod_power_terminal.gsc`, `[TOD_POWER_TERM]`). Its body clip runs floor to roof (no perch); the
  trigger stands 24 in front of the face, outside the clip.

### 4. The Cyber Teddy (Map One's v19.64 + its 2026-09-24 melee lane)

The song hunt's three bears (`_tod_secret.gsc`) wear a fan's Cyber Teddy (`tod_cyber_teddy`, made
with Meshy AI; `art/cyber_teddy/`), replacing the stock mystery-box bear. Its numbers are ONE chain
held by `tools/cyber_teddy/verify.py`: `TOD_SECRET_LIFT` 14.0 / `_HALF_DEPTH` 7.9 =
`haven_layout.js` `BEAR_LIFT` / `BEAR_HALF` = the manifest; `BEAR_EXT` (its half extents) is
asserted against the haven walls and rails, which moved the floor-20 corner bear 3.4 units off the
loggia's east rail (`BEAR_SIDE` 11.4; its arm reached into the rail). **A blade swing now counts**:
a melee notify finds a live bear within 120 of the eye, in front of the swing and in sight
(`melee_watch` / `melee_hits_bear`, `[TOD_SECRET] melee:`) - the Warrior has no gun to shoot one
with, and the bear has no hit collision. All three bears here stand on a floor, so all three are in
reach.

### 5. The cyber Rampage Inducer and its stings (Map One's v19.68m + v19.68x)

The BO6 essence canister is replaced by Map One's own cyber inducer (`tod_inducer_cyber` + `_on`:
44 x 44 x 67, five animated bones, two seamless looping clips - idle 12 s, on 3 s - via
`animtrees/tod_inducer.atr`; `art/rampage_inducer_cyber/`). OFF wears cyan standby trims and a dim
amber core, ON turns rampage red; the sparks fly off its two front claw tips; the lamp moved up to
the crystal (`gen_tod_inducer_fx.py` SPAWN_Z 35). It stands on the crown balcony (the base arena is
the fallback), so the generator cuts its collision THERE: a 42 x 42 body clip 40 tall and, 20 above
it, a steep cap rising away from the pad; the centred use-trigger rides in the slot between them
(`crown_inducer_trig_lift()` / `base_inducer_trig_lift()` 44). Every flip plays the device's own ON
/ OFF sting from the device (`tod_rampage_on` / `_off`, `tools/rampage_sfx/`), and the stock
purchase cha-ching is gone from the flip. Gates: `tools/inducer_cyber/verify.py` (pre + post link),
`tools/rampage_sfx/build_rampage_sfx.py --check`. Logs `[TOD_RAMPAGE] MODEL / ANIM / STING`. The
canister's files stay on disk unzoned as the rollback (the zone comment has the steps).

### 6. Widow's Wine's powered panel (Map One's v19.43)

The SAT Widow's Wine machine's powered panel material is authored on
`lit_emissive_scroll_3layer_advanced_fullspec`, a techsetdef neither install had; the linker builds
it on `missing_techsetdef_geometry` without a word and the whole front panel draws the engine's grey
stand-in once powered (TOD II's 2026-10-02 and 10-03 ledgers: exactly that one row). The def (Map
One's file, stock shader sources only) now ships in `share/raw/techsetdefs_stable*` and syncs into
the private root (real folders, no junction). Post-link gate: zero `missing_techsetdef` ledger rows.

### 7. The Heavenly Altar (Map One's v19.66 + docs/167 item 16)

`waterRoughness` 0 on its material (fullspec maps it to the emissive layer's depth; the altar
profile now carries it, like the teleporter's), and its crest LODs: the first switch at 1000 (was
260; the crest emblem breaks from LOD2 on), every switch after it in order. The installer
regenerated the GDT + manifest; the seven LOD binaries came out byte-identical.
`heavenly_altar/verify_native.py` gained Map One's LOD assert.

### 8. The packed 870 aims down drawn sights (Map One's v19.22)

`noOptic()` did two of Map One's three edits: it cleared the optic and borrowed the base's ADS
clips, but left `hideTags`, so all four packed 870 forms hid `tag_sights` and raised to iron sights
nobody drew. It now takes the base form's sight tags (`''` for the 870); the regenerated weapon file
differs by exactly those four lines (182 assets either way). Gate: `tools/test_no_optics.js` (Map
One's, retargeted: the Breacher's three guns, plus every packed form against its base).

### 9. The perk machines (Map One's v19.32 + v19.45 + v19.48 + v19.48b)

Double Tap's cowboy really fires his sixteen authored shots at the zombies in front of the machine
on purchase (aimed, credited to the buyer, never his held-weapon procs; the power scale takes its
tenth at the front door), the fourteen recovered machine WAVs, Wisp Tea's activation audio, and the
cue cleanup on interruption (`_tod_perk_anims.gsc` = Map One's module minus its spire retire lane).
The clips and skeletons live in MAP-OWNED `tod2_perk_machines` folders: the private root's
`model_export\tod_perk_machines` is a junction into the shared install. Gates `test_perk_anims.js`
+ `verify_perk_machine_presentation.py` (pre + `--ledger` post). Logs `[TOD_PERK_ANIM]`.

### 10. Nine small fixes

1. **RK5** (v19.55): `level.super_ee_weapon = level.start_weapon`, and a picked-up RK5 is reaped like
   a foreign sidearm (it rode as an extra gun and won stock's last-stand pistol pick).
2. **Round-end stinger** (v19.55): gone from the endless round wait (it played every round).
3. **Gift of Death pickups** (v19.53b): the free PaP bottle and Zombie Blood are no longer refused
   while you hold the Gift (`drinking_besides_powerup_gun`).
4. **Nuke and riot-shield kills pay** (v19.58): `nuke_kill_pay` / `equipment_kill_pay` through
   stock's death points (the haven quarter still applies).
5. **PhD Flopper** (F16): only your OWN explosives are zeroed; the Mangler cannon and the
   Doppelghast death blast land again.
6. **Pack-a-Punch refuses the riot shield** (F12): `tod_pap_refuses()` at all three sites.
7. **Zombie Blood's end** (F15): keeps invulnerability that another holder still owns (world pause,
   the spin, the class terminal, the Dealer's house shield, the parked finale).
8. **Prompt UI**: a blank hint hides every card (`Active_1x1`), and three unused prompt widgets now
   close their children (300 / 275 / 275 leaked elements over 25 lifetimes in a harness, 0 after).
9. **Chat hides with the scoreboard** (v19.68): both chat containers follow the board and the veil,
   never the pause menu.

## Not ported (they do not apply here)

The Mage is gated off (`TOD_MAGE_ENABLED` 0): every staff, Archmage, Healing Aura and ice/fire
balance entry waits for it. The Endless Spire, the Warden trials, the Warden King, PACK II/III and
the spire HUD are gone from this map. The Skirmisher / Assault / Heavy / Slasher rosters were
replaced (no Enfield, Krig, AK, MP7, Mk 48, HK21, UDM, nail gun, bat class). Map One's ATHLETE
wall-run perch pass (v19.71) answers a class this map retired; its idea is used where it matters
here (the new props' steep caps).

## Backlog - each is the user's call

- **Co-op restart** (v19.59 / v19.63 / v19.68b-d): Restart is hidden in co-op here and runs
  `map_restart` on the pressing machine. Map One's unit is large and was proven only with a local
  bot.
- **One damage number per zombie** (v19.47): the per-victim event lane; frees 15 bits of the full
  61-bit clientuimodel pool.
- **Death Perception outlines every enemy** (v19.72): here it still skips anything flagged as a
  boss, and the live Doppelghast and Mangler are.
- **Rampage on the tower** (v19.68j/k): the core's lit strips burn while Rampage is on, plus a
  shockwave at the switch. The strips are unlit kit panels here and the core opens at the havens;
  needs a descent-aware design.
- **Luck souls** (v19.33 / 34 / 40): souls you collect instead of direct luck credit.
- **Zombie Blood screen filter** (v19.65): it would outrank the Necromancer's cloak overlay.
- **Door posts on the railing line** (v19.57): closes a slit beside every lap door; moves the
  conduit wall mounts (a conduit regen) and may touch the Dealer panel's review.
- **Crate prompt on the long sides** (v19.55 #5): a 100-radius trigger breaks the haven spacing
  asserts; needs a machine move.
- **End-of-game stats board** (v19.55 #6), **the gauge pip filter** (v19.46), **the party rows**
  (close ranks, teammates' shield bars, the local row gap), **the floor label** on the scoreboard /
  pause, **melee inspect + lunge recovery** (v19.68), **the weapon-switch card lane** (v19.68).
- **Hit markers on the cowboy's hits**: TOD II's `_tod_killconfirm::hit_cb` marks every enemy hit,
  so Double Tap's volley will flash markers on the buyer's crosshair (Map One never did). A one-line
  inflictor check if unwanted.
- Tooling: the language-pass WAV-flake retry and bank-shrink guard (v19.66), the init-flag lint
  (v19.65c), retiring the still-zoned `t9_krig6` / bat weapons and DEADSHOT's leftovers.
- **Credits**: Nikolai (the props) and the Cyber Teddy's fan author / Meshy plan are still to be
  confirmed in CREDITS.md before a public upload.

## Build

- **Landed 2026-10-04 12:05** (36 files edited, 121 new), the map regenerated. `python tools/run_build_gates.py`
  on the repo: 123 gates, 0 failures (480 s).
- **FULL build 1 (12:15, `tmp/map1_migration/full1.log`) died at `gdtdb /update` (12:16:41).** Two of this pass's
  generators wrote `//` comment lines into their GDTs (`tod_floornum.gdt` lines 2 + 4608; `tod_fan_props.gdt`
  lines 2-4 and its section headers). gdtdb read the first as "Adding KVP to unnamed entity", the rest as
  "Unknown token", and exited 1. Nothing compiled or linked; the deployed `.ff` stayed -7a's 11:58:38. No gate
  runs gdtdb, so the 123 green gates said nothing about it.
- **The fix:** both generators write no comment line (`tools/floor_numbers/make_assets.py`, the land kit's
  `build_fanprops_kit.py`); each regenerated GDT is byte-equal to the old one minus its comment lines;
  `tools/fan_props/manifest.json`'s `gdt_sha256` follows. **NEW GATE `tools/lint_tod_gdt.js`**, before the sync
  on every build: GDT syntax (the brace, the blocks, the brace; no `//` line; every key has a value) and one
  asset per NAME + TYPE across every repo GDT (the namespace is per type: 84 same-name pairs in the stock GDTs
  are all two different types, zero same-type repeats). It plants 10 syntax errors and 3 duplicates in memory on
  every run and fails if it misses one. Clean on our 74 GDTs; over the 531 stock GDTs it flags only Map One's own
  comment lines and two malformed third-party packs (`mechz_spiki.gdt`, `wpn_t8_zmb_freezegun.gdt`), none of them
  in this repo. Map One's comments never stopped Map One because its `build_map.ps1` only WARNS on a non-zero
  gdtdb exit ("new GDT assets may not link"); this map's DIES on it, so a GDT copied from Map One must be
  comment-free here.
- **BUILT in -a4's combined FULL BUILD OK 12:46** (`tmp/haven_v5/full1.log`; started 12:31:58; it carries this
  pass and -a4's haven v5): `.ff` 12:46:36, FF 233,280,000 B, a FRESH compile + bake (BSP + navmesh 12:40:38,
  LED 246,277,485 B, NAVMESH GATE OK), the 8 known-waived linker lines only. Inside it, the gdtdb step passed
  ("asset DB refreshed") and every gate of this pass printed OK: FLOOR NUMBERS ASSETS, FAN PROPS + FAN PROPS
  LEDGER (12 models / 12 materials / 21 images, no usage or techset complaint), CYBER TEDDY + its LEDGER (9,919
  triangles, the material complete), INDUCER_CYBER (pre-link and against the compiled ledger), RAMPAGE_SFX,
  test_no_optics, test_perk_anims, PERK MACHINE LEDGER, and zero `missing_techsetdef` rows.
- **Verified here after the build** (scratchpad `verify_migration_build.py`, read only): the 12:46:36 ledger
  carries all 80 migration rows (Nikolai's props, the teddy, the inducer + its anim tree and clips, the perk
  machine clips and cue effects, the five `wc/tod_floornum_*` materials at 1,368-1,592 B each = complete, and
  their image `i_tod_floornum_c`); every other zone scriptparsetree; all 19 sound files of this pass are in the
  banks (14 perk machine + 1 Wisp Tea + the two inducer stings in the loaded bank, Wisp Tea's jingle and
  stinger in the streamed bank, as their rows say). At 12:48 the deployed scripts / ui / zone_source equalled
  the repo, nothing was deployed after the `.ff`, and no repo input was edited after the build start (-b6's
  docs/209 landing at 12:52 is newer than this `.ff` and rides the next build). UNPLAYED.
- **SUPERSEDED AS THE TEST .ff by -b6's FULL BUILD OK 13:34:58** (`tmp/dealer_gift/full2.log`; started 13:22:25,
  `.ff` 13:33:10, FF 233,681,472 B; geom_key reused the 12:43 bake; it adds -b6's docs/209), verified the same
  way: GDT LINT OK ran inside it before the sync, every gate of this pass printed OK, all 80 migration ledger
  rows, every other zone scriptparsetree, zero `missing_techsetdef` rows, 19 / 19 sound files in the banks,
  deployed = repo, nothing synced after the `.ff`, no repo input edited after its start. UNPLAYED.
- **Three false alarms in that check, for the next agent:** an image's ledger name is its GDT asset
  (`i_tod_floornum_c`), not its PNG's file name; the sound banks index WAV STEMS, not alias names (aliases are
  hashed), and a `streamed` row lives in the `.sabs`, not the `.sabl`; the ledger never lists HB21's
  stock-path override `scripts/shared/ai/systems/animation_state_machine_utility.gsc` (on disk since Sep 10,
  zone ~2298), so its absence there predates this pass and says nothing about it.
- **The new gate is wired:** `tools/lint_tod_gdt.js` in `build_map.ps1`'s pre-sync block (after the weapon-cost
  gate), on the repo 12:54, coordinated with -b6's landing; `run_build_gates.py` runs it.
