# Tower of Doom II: Fallen Cybercity — session brief

> **HOW THIS FILE WORKS.** This file holds only what binds every session: hard rules, the user's standing direction, how to work, and where things are. Dated status notes live in **`docs/status_log.md`**, newest first: what was built when, sizes, hashes, verification evidence, UNPLAYED lists, the current test .ff. Add a new status note at the TOP of `docs/status_log.md`, never here. If a rule here changes, edit it in place. Keep this file small: every session and subagent reads all of it.
>
> The durable sections below ("THE QUALITY BAR" onward) were partly written for Map One / TOD1 (the climb, the Endless Spire, the old finale, five classes, `zm_tower_of_doom` paths). **Where they disagree with this top part, this top part wins.** The dated `### 2026-09-26 …` subsections in those durable sections are status notes, and their "Archer clearance" lines no longer apply.

## HARD RULES

1. **Keep Tower II isolated from Map One** (user 2026-09-22; docs/154). Map One = TOD1: repo `c:\Users\jorda\Repositories\tower_of_doom_cybercity`, map `zm_tower_of_doom`. This repo owns ONLY `zm_tod2_cybercity` and the private tools root `C:\BO3Tools\TOD2Cybercity`, which `.tod2-workspace.json` binds to this repo. Run `tools/setup_tod2_workspace.ps1` once. After that, use only the guarded build/sync tools.
   - Never deploy as `zm_tower_of_doom`. Never write to:
     - Map One's repo or usermap.
     - The shared Steam Mod Tools database, sources, caches or outputs.
     - Any other map.
   - Never repoint the global `usermaps` junction. Only our own child junction may point at our output.
   - Never build `Repositories\test+map`: its `build.ps1` compiles into the shared Steam root.
   - The private root contains about 80 `model_export` folders that are junctions to stock folders, including `tod_perk_machines`. They are READ-ONLY. Copy a folder before editing it and give the map-owned port a new name (`tod2_*`), or the sync dies on the isolation guard. Never hardlink mutable assets.
   - TA_* compiler variables are process-local: never `setx` / stock `modtools_setenv.bat`. Never reuse Map One's PublisherID `3788921059`. A Tower II request never authorizes changes to another map.
   - Map One is READ ONLY. Port its built outputs byte for byte, pinned by its manifests. Never run a Map One tool from here, because it hardcodes Map One's repo and the shared tools. Retarget the tool first. (docs/208)
2. **The user tests. Never launch the game unasked.** Write the code and the logs, build, then STOP. The user plays, and you read their `console_mp.log` (archive it with `tools/capture_ai_logs.ps1`). "Verify" means read logs, not launch the game. Use `tools/run_game.ps1` only when the user's message explicitly asks for an agent-run match.
3. **Never build, sync or send input while BlackOps3 runs.** If the game appeared during a build, that build is void. Never close the user's game, another session's Blender/Radiant, or their dialogs.
4. **Read `docs/BO3_MAPMAKING_KB.md` first.** It is our copy, so record new lessons here.
   - In the durable sections and old tool comments, "map 1" / "the old map" usually means the user's ORIGINAL map **ACC** (`c:\Users\jorda\Repositories\abandoned_cyber_city_zombies`, prefix `acc`), not Map One.
   - Before touching stock interfaces, consult ACC: its CLAUDE.md, docs/14 (stock-API traps) and docs/16.
   - Write to neither repo, and never re-learn a lesson ACC or Map One already paid for.
5. **No session is lead** (user 2026-09-27, repeated 09-28). You need no build clearance, shared-file approval or lead relay. Every "Archer lead / awaiting clearance" line no longer applies, including those in docs/crown_alarm/BUILD_HANDOFF.md. Peer sessions share this repo all day, so builds run one at a time (see "Builds, gates, peers"). Never hold finished work back: it goes into the next build, and only a running game delays it (arm a watcher).
6. **Voices:** never feed a real actor's recording to a voice model (clone, reference audio, speech-to-speech) without the owner's documented consent. The Dealer is his own entity: nothing of Richtofen (head, lore, voice, or the retired consented clone). `tools/dealer_boss/test_dealer.js` s7b fails on `richtofen` / `c_zom_der_` / `mtl_c_gen_` / `_unmasked` names.
7. **Publish safety.** Before publishing, every `level.tod_dev*` / `tod_god` is false and every harness is parked; re-read both in the DEPLOYED tree. The full checklist is under "Builds". All dev flags have been false since 2026-10-04 (the first real playthrough).
8. **Never GPU-render the sky while BO3 runs** (8 GB card; use `-Device cpu`). Never run heavy Blender exports or denoising during a Radiant bake (see the durable "Shared workstation memory" section).
9. **Never `git stash` here.** Stash/pop rewrites line endings and breaks sha-pinned gates.
   - Files here are LF, CRLF or mixed, so a scripted edit keeps each line's own ending.
   - Edit gate, GSC and regex-bearing files with Edit/Write. Never use a bash heredoc, `python -c` or `printf`: each one collapses a level of backslashes.

## User direction

- **Quality bar, model surfaces, how to end a response, matching effort to the question:** see the durable sections below. **Finish every task** the user stacks mid-turn.
- **Self-serve assets since 2026-10-04:** the session that needs an asset makes it (`tools/artgen/README.md`). Send the user a zip only for game rips, licensed music, or picks they must make by ear or by eye.
- **The Fall / descent** (docs/160): spawn at the top and descend 50 floors. The run ends at the Undercity/base; the ending is not designed yet.
- **Dark until the power** (docs/164): no world emission; light comes only from light entities. The alarm lights the crown hall (`HALL_ALARM_LIGHTS`, Radiant State 3 via `set_lighting_state(2)`). Everything else waits for the power wave (`lightingstate1`, then `set_lighting_state(0)`). Tune lights, SSI and skyStops, not glow. **No tower fog** (`TOD_VEIL 0`).
- **The power switch gates everything except the crown PaP** (user 2026-09-25). These wait for `power_on`:
  - Perks (solo Quick Revive is stock's exception).
  - Teleporters.
  - The Black Market, which is live from the first frame only under `tod_dev`.
  - The balcony door and the jump pad (`refuse_reason` "no_power").

  The crown PaP wakes at the alarm (`level.tod_crown_pap_live`). Nothing paid may stand between spawn and the first zombie.
- **Only regular zombies** (`level.tod_only_zombies = true`). Deliberate exceptions: the crown ramp (`_tod_fall::hunters_watch`), `_tod_cyber_elites`, haven guardians and arena waves. The four Map One directors it switched off (Panzer / Rogue Protector boss, Fury, hellhounds, armored sprinter) were retired whole on 2026-10-05 (W2E); the flag now gates nothing and is the contract a new director honours.
- **Four classes.** Their keys: Archer `assault`, Breacher `heavy`, Warrior `slasher`, Necromancer `necromancer` (class id 1). The old key `skirmisher` is retired everywhere.
  - All four move at `TOD_CLASS_SPEED_ALL` 1.1 until the user says otherwise.
  - **No secondaries.**
  - **No perk limit** (`level.perk_purchase_limit` 16; the PERK SLOTS card stays retired).
  - The Mage is RETIRED WHOLE (user 2026-10-04: "There is no mage class at all"). Its module, staffs, cards, art, sounds, effects and tests are in `archive/mage_retired/`. Four classes ship; never revive it. `TOD_CLS_COUNT` lives in `_tod_class_count.gsh` (LOCKSTEP `CLASS_N` in tod_class_select.lua, gated in build_map.ps1). Ids 49-56 are free (docs/upgrade_ids.md).
- **Rails and barriers:**
  - Visible rails stay LOW, with full-height invisible clip behind them (user: a tall rail hid the tower). Balcony curbs are 12u and tower rails `RAIL_VIS_H` 39 (`RAIL_VIEW_SCALE` 0.7). Each rail's clip runs from the floor to 168u. Never raise a visible rail to fix collision.
  - **Invisible barriers, never an invisible roof** (user 2026-09-26). Every wall, post or roof that bounds play carries a `clip` column up to `BARRIER_TOP` (`SKY_TOP` - 300), and every new room gets the same. The one exception: spiral rail caps stay at `RAIL_CAP_H` 112 (the user's call).
  - Players may jump down the tower.
  - The Archer's grapple has its OWN invisible wall at the play area's edge (the zone volumes, docs/218_archer_auto_bow.md): velocity only, on the rope and in the air after it, never a roof, never another class. A hook outside the play area is refused.
- **Cards:**
  - One core-weapon card per class (`core_weapon_bonus`).
  - Stepped cards are 9 levels, with the steps at Lv3/6/9.
  - **No weighted cards** (`TOD_TIER_W_*` 1, `TOD_TIER_R_*` 1.0).
  - No rarity step may buy nothing. Bonuses add per level.
  - A card change updates all of these in one pass, in simple words:
    - Its description.
    - The pause and scoreboard rows (tod_upgrade.lua DOMAIN/DETAIL).
    - Its layered card art: `install_card_art.py --check` fails when a class is dealt a card with no art, which breaks every peer's build.
    - The live armory page `docs/tod2_armory.html`: republish it to https://claude.ai/artifact/Euf1fzyYWgez5NcxxNT4Sq (the old UUsGQZ… link is dead) and run `node tools/verify_tod2_armory.js`.
    - The `docs/armory.html` workbench (`verify_armory_*.js`, advisory).
- **Never port Hellbound's kill feel** (`test_ability_fx.js` §D fails it). Kill feedback = `_tod_killconfirm` (punchy hit markers on every enemy) + flings. `tod_killconfirm::ding()` is the only code that plays `tod_headshot_ding`: the shooter's headshot kills, elite/boss kills and the lucky meteor, at most once per frame.
- **Every class's lethal, tactical and weapons get sound AND visuals.**
- **Havens** (docs/202): the haven is the whole hall, with the machines inside FACING THE TELEPORTER (user 2026-10-04: facing out "is just wrong"). A haven must be taken by force.
  - v6 (user 2026-10-04): nothing of it may be seen until you are on its floor (walled loggias, walled galleries; the porch arch is the one view in). The way down leaves ACROSS the field: a sunken stair from the hall's north-centre, the W flight blocked by debris under the porch. The floor's door is SEALED until the haven is taken (`level.tod_haven_door_seal_fn`; a dark haven seals nothing).
  - It boots CORRUPTED: a red wreck, the screen dark inside (`TodHavenDark` + 2D non-looping `tod_haven_dark_in`/`_breath`), a bullet barrier both ways, and guardians that stay inside.
  - While corrupted it gives NOTHING: no enemy slow, no damage reduction, no kill-pay cut, no bleedout extension. Its pad and the floor-40 arena gate are dead (`level.tod_haven_locked_fn`).
  - Every guardian must die (`TOD_HAVEN_GUARD_*`; one more Doppelghast for 3-4 players). The last death purifies it in one animated ~4.5 s sequence (`tod_haven_dark_lift`) and pays every player `TOD_HAVEN_CLEANSE_PTS` 500.
  - SAFE = a cyan lattice:
    - Enemies move and swing at x0.67.
    - Players take x0.67 of ENEMY damage (never falls or self-damage).
    - Kills pay x0.25 to a payee standing inside (`level.tod_haven_kill_pay_fn`).
    - Bleedout lasts x1.5 (`TOD_HAVEN_BLEEDOUT` = TodHealthTint `BLEED_MULT`).
    - The spawn rest applies only inside a TAKEN field (`level.tod_haven_calm_fn`).
- **Battle Arena** (docs/185): no camp spots, every level reachable on foot, no fall damage in a fight, and a badge reading BATTLE ARENA / LEVEL n. **Level 10 = the Dealer's House** (docs/207): a cursed LAST ROLL while he laughs, then the players are drained to 1 HP but cannot die, and they fight only him, in two phases.
- **Rampage** can be toggled all match; never re-add a round seal. It is the HARD mode (user: "rampage feels easier"), so any knob that eases the game keeps a rampage branch:
  - Elite roof +3 (`TOD_RAMPAGE_ELITE_ROOF_ADD`).
  - Zombies +10 (`TOD_RAMPAGE_AI_LIMIT_ADD`).
  - Elite HP x1.5 (`TOD_RAMPAGE_HP_MULT`).
  - Horde HP x1.2, applied only through `_tod_zombie_speed::rampage_horde_mult()`.

  Gate: `tools/test_rampage_levers.js`.
- **The Dealer** (docs/198, 199, dealer_identity.md): black hood, charcoal mask, red X eyes, stitched grin.
  - STATE ONE (masked) levitates and holds the scythe in both hands.
  - At half health (`TOD_DEALER_MASK_CRACK` 0.5) the mask CRACKS. STATE TWO walks the ground set and carries the machine gun (one `zombie_arms_position` write plus the body swap).
  - His own full voice, never whispering. The default voice stays unapproved until the user picks one.
  - Never retune `mask_tone.py` unasked: the user called it final. `CYBER` 0.45 was asked for; go to 0.25 only if asked; 1.0 = v5. Keep v5's open top end, because muffled words were the complaint.
- **Black Market:** players only ever see the name "BLACK MARKET". A player's first use without a companion is **the Dealer's Gift** (docs/209): a free companion, with no luck or points spent. The 8 Vault parts and the bench prompts stay retired. The companion freezes with its owner; a downed owner releases it.
- **Near misses:** roll every result FIRST at the odds shown. A near miss only decides what is SHOWN around the result; never show a prize and take it back.
- **Sky** (docs/166): the v10 middle ground (`art/sky3d/middle_ground_review/concept.png`), never the skull gate.
  - The close buildings set the material family for the whole skyline. Planets keep their surface detail.
  - The title is the scariest focal point. It carries the Dealer crest, is baked DULL, and goes bright only after the first-jump crash.
  - Every sky pass keeps the approved composition:
    - All 8 placed hero towers.
    - 1,189 ordinary lots / 1,222 building groups / 18 sky groups.
    - The Skyrail station.
    - Every planet/ring/moon group at least 3.16 deg above the measured skyline.
    - The FIXED gain 0.016525428679573573 (`finish_profile.json`).

    Prove it with the pass's `audit_composition.py` / `skyline.py` / `clearance.py`.
- **First jump** (docs/196): nothing sits on screen too long. Lengthen a moment with a dwell, never by stretching the flight. The pad wears Der Eisendrache's jumpsphere and keeps the same behaviour (docs/163).
- **Music:**
  - 50% bass cut; bands at -11.5 LUFS.
  - Going down: Champs 50-42, With You 41-34, Cornfield 33-26, Una Mattina 25-18, Reykjavik 17-9, Meteor Herd 8-ground.
  - Intro until the alarm, then silence. The first band starts when a living player steps onto the JUMP-PAD BALCONY (`jumppad_balcony_mins/maxs`; user: "No mid air on the jump pad").
  - Use the instrumental the user chose, official or not (Meteor Herd = the Internet Archive "Instrumental Attempt" FLAC). Never separate vocals unless the user authorizes it. With You was authorized: a BS-RoFormer + MDX23C average plus a synth melody layer.
  - Licences (CREDITS.md) are the user's call.
- **Typeface:** never restore the retired face (`archive/typeface_retired/`). Class art = docs/171 Theme B. Prompt sizes = v19.7: title 11.4 / detail 8.4 / footer 9.4 / price 10.4; left HUD 1.035.
- **Health bars:** elites/bosses RED; Necromancer helpers WHITE, showing how much health they have left.
- **Lucky clover** wears stock `mtl_x2icon_gold`. The golden zombie's glow stays subtle: 0.45 x 2.2, halo 70 u / 0.2, light r140 i300.
- **The Recall** returns a player only after a fall off the map, at 1 HP. Drops, perches and standing below unbought doors are allowed.
- **Heavenly altar:** less gloss, never matte.

## Current state

Test .ff and unplayed list: `docs/status_log.md`. These paths replace every `zm_tower_of_doom` path below:
- Entry: `scripts/zm/zm_tod2_cybercity.gsc|.csc`
- Modules: `scripts/zm/zm_tod2_cybercity/`
- Zone: `zone_source/zm_tod2_cybercity.zone`
- Map: `map_source/zm/zm_tod2_cybercity.map` (GENERATED)
- Deployed: `C:\BO3Tools\TOD2Cybercity\usermaps\zm_tod2_cybercity\`

| System | Now (key code) | Doc |
|---|---|---|
| Opening | Crown hall: PaP east shrine, the LIVE Black Market west shrine (`CROWN_SHOPS[0]`), alarm button at the centre. Intro until the button (`TOD_FALL_LEVER 1`, stock `spawn_zombies` flag). The siren winds up at once and LOOPS (wind-up/loop/wind-down, `make_siren_clips.py`) until the 5000 gate is bought or the crown seals. Spawns 10 s after the press; crown PaP wakes. 5000 gate (`TOD_FALL_GATE_OPEN 0`) -> hallway: power room (GRID TERMINAL), teleporter room, balcony (jump pad, QR, a dark display Black Market hut that `TOD_SHOP_CYCLE 1` never makes live, inducer). Power wave top-down, then `set_lighting_state(0)`, then the seal. Crown ramp hunters (`_tod_fall`) | 160, 163, 164 |
| Descent | 24 broken drops (`broken_tower_layout.js`, down-only for zombies) + 26 paid doors. DESCENT defines stay in step with `gen_tower_map.js DESCENT`. Tier 2 at floor 40, tier 3 at 20. The old finale was retired whole on 2026-10-05; the crown's props and open road are `_tod_crown_props` | 160, 208 |
| Spawns | Endless rounds; `TOD_SPAWN_MULT` 0.70; THE AMBUSH 30->60%. Cap 36 solo + 6 per extra player (max 54; rampage +10 under the 58 ceiling; actor gate 60 of 64 minus live allied actors) is the LATE cap: THE RAMP (user 2026-10-04) lets a third stand on round 1, all of it from round 30 (rampage 15), trickle x1.6 -> x1.0 on the same rounds (`ai_limit_now`, `spawn_ramp_mult`). Elite HP x4 (`TOD_ELITE_HP_MULT`). Charcoal horde + round elites (`_tod_ambush`, `_tod_cyber_elites`) | 204 |
| Pursuit | `_tod_reach`, `_tod_stray` THE HUNT, `_tod_recall` rev 2 | 200 |
| Power scale | Player/partner hits x0.1 at the damage entry point; GDT DPS stays in old units (`_tod_power_scale`) | — |
| Cards | 6 class cards + DR/LUCK/BOUNTY, 9 levels each; COMMON..LEGENDARY +1..+4; THE PULL; layered v2 for all four classes; luck + hot streak | 187, 193, 201 |
| Havens v6 | Floors 10/20/30/40: corrupted -> purified -> safe; walled; sunken-stair exit; door sealed until taken; floor-40 pad = arena gate (`_tod_haven`, `haven_layout.js`) | 202 |
| Battle Arena | 10 levels x 3 waves, director, overcharge, level badge; level 10 = `tod_house::run` (the Keeper and the `TOD_ARENA_HOUSE` toggle retired whole 2026-10-05) | 185, 207 |
| Black Market | One active shop; 2500 spin, 30 tiles, 3 slots per companion, near misses, the Gift, class-aware VO (`_tod_shop`, `TodSpinReel.lua`) | 188, 198, 209 |
| Wunderstrahl | The laser power-up gun (the DG-2 remodelled): shares the Death Machine slot 50/50 with the Gift of Death, 30 s, no overheat; a gas weapon whose ENGINE beam draws from tag_flash; script damage pierces (`_tod_wunderstrahl`, `tools/wunderstrahl/`) | 219 |
| Companions | Protector / Talon / R.A.P.S. / Cerberus, one per player, from the Dealer's Gift, rebuild 45 s; every deploy arrives via `arrive_fx` (`_tod_partners`) | 156, 209 (159's parts flow superseded) |
| Luck sources | Clover, shootable lucky meteor, one golden zombie per round; kill luck 12 | 197 |
| Teleporters | 750 per use (arena free); departure hall (`tower_transit_layout.js`); off/ready/recharge states | 152, 196 |
| Jump pad | DE jumpsphere; one-way 7 s flight; first flight = 12.1 s crash scene + lit sign card (`_tod_jumppad`, `_tod_jump_title.csc`) | 163, 196 |
| Sky | Cycles city v10 + consistency + Dealer crest; `skyRotation` 40 / `skyStops` 4.35; client fleet v4; war in the sky | 166, 192, 205 |
| War damage | Client rubble at the breaks, torn conduits lit by the wave, scorched faces | 205 |
| Ability FX | One owner, 1p + body halves, actor hit lane (`_tod_ability_fx`) | 203, 206 |
| UI | HUD/pause/scoreboard V2, `TodPromptCard`, HUD veil, the red Fallen theme (ONE switch: `tools/artgen/synthwave.py` THEME; synthwave kept), `TodToast` (team / tier lines in our typeface), typeface + TTF | 172, 180-184, 218 |
| Map One port | Floor numbers (on the paid doors only since 2026-10-05), fog fix, Nikolai's props, teddy, inducer, `tod2_perk_machines`, nine fixes, backlog | 208 |
| Crown art | Convex crown, material kit, red alarms, power conduits | art_cohesion/ |
| Tester kit | `TOD_TESTER_KIT 0` (class terminal + arena level-10 start only when 1) | — |

**Retired, parked or switched off — do not revive:**
- Endless Spire, Warden Trials/King, harness #8, spire gauge.
- The Mage (retired whole 2026-10-04, archive/mage_retired/); the old finale and the Keeper boss (retired whole 2026-10-05, archive/map1_carryover/, ledger `_landed_w2e.json`; the Dealer keeps `_tod_keeper.gsc`'s archetype half and the Keeper clips his anim table names).
- The 8 Vault parts, the 4 workshop bench prompts, the "partner part" noun/icon, and the "companion required" card + its 2 VO lines. KEPT: the crown TEST benches behind `TOD_PARTNER_TEST_BENCHES`, the 4 crafting tables, and the 8 part models (the installer pins these).
- The Hellbound kill feel; dark upgrades + overcharge (`TOD_DARK_ENABLED 0`); PERK SLOTS; the DAMAGE card; secondaries; the Skirmisher.
- The crown altar; the overlook.
- Static sky ships/asteroids; the fleet warp; the fog veil; `fx_jt_veil`; `tod_jump_reveal`; the skull-gate title.
- The rampage seal; "Item Shop"; the old typeface.
- Panzer/Protector/Fury/hound/sprinter directors, retired whole 2026-10-05 (W2E) with their packs, zone lines and gates; the 8 parked cards (SPRINT FIRE, SCAVENGER, FIRE RATE, HANDLING, RUN AND GUN, SECOND WIND, SOUL SIPHON, TRAILBLAZER) too (their ids stay mapped). `tools/test_retired_systems.js` keeps them out.
- **Before retiring anything, grep the private root's installed packages** (`C:\BO3Tools\TOD2Cybercity\share\zone_source\*.zpkg`): a stock package can name repo files. `zm_ai_zod_companion.zpkg` (the Civil Protector companion) names the `_hb21_zm_craft_fuse` scripts, `p7_zm_zod_fuse` and the `zmb_zod_fuse_*` aliases, so they stay (2026-10-05).

## Rules by topic

### Builds, gates, peers
- **Before building:** make sure BlackOps3 is closed and no build is running.
  - Check processes AND fresh `tmp/*/` logs AND usermap sync mtimes.
  - A powershell parenting a `-s -NoLogo` job host is a build (modlauncher is not).
  - Queue behind a quiet-wait wrapper. Honour peer requests (including Map One's) to hold linkers.
- **There is no gates-only build switch:** run `python tools/run_build_gates.py` on the repo before a FULL build, and check its `gates:` count.
- **Landing:**
  - Stage a multi-file pass in a scratch mirror and land it in ONE step (anchors asserted, a 3-way merge that keeps every peer hunk).
  - Wire shared files LAST, right before your build (`wire.py` per feature).
  - Keep un-wired work OUTSIDE gated paths. The lints scan all of `scripts/` and `ui/`, and each generator's `--check` scans its own fx/sound/art output (30 un-zoned generated effects once failed a peer's build).
- **A gated path must be self-consistent at every instant.** After a fix, prove the gates and send peers "TREE SAFE". A new gate that asserts a generator's output lands together with the regenerated output. Gate runs in a mirror write receipts through junctions into the repo, so while a peer builds, run only gates that write nothing.
- **Never edit gated files, regenerate gated outputs, or change build inputs while a peer build or watcher runs:** gates read the REPO after the sync. Before editing under a waiting `build_when_idle` watcher, confirm it has not started, stop only that watcher, then re-arm it.
- **A peer's broken asset aborts every linker:** ping the owner and report "synced, not linked". Never add a bypass switch to `build_map.ps1`.
- **Build type:**
  - Use a FULL build for any `.map`, brush, world-material, GDT, image, sky or weapon-GDT change. `-GscOnly` is only for scripts, zone and Lua.
  - `geom_key.js` reuses an unchanged bake (`show` says why it re-bakes). `-ForceBake`/`-Publish` always bake.
  - A FULL build that baked and then died at the linker can be finished with `-GscOnly`.
  - A build that synced before a fix carries the old tree.
- **Flakes:** on a `Missing source checksum` for a wav, rerun once, then compare the printed `sound bank:` size with the last good build (a truncated bank still prints BUILD OK). If BO3 launched mid-build, clear the generated sound/zone cache and rebuild clean. A linker ASSERTION dialog hangs the build silently: read its window title.
- **Pre-publish:**
  - All `tod_dev*`/`tod_god` false, `TOD_PARTNER_TEST_BENCHES`/`TOD_DEALER_TEST_SPAWN` 0, `TOD_MOCK_PARTY` false (`-Publish` refuses each of these). `TOD_TESTER_KIT` is 0 unless it is a testers' release (`-Publish` only warns).
  - Turn off every logger that prints while dev is off: `grep -rnE "#define TOD_\w*_LOG\s+1" scripts/`, and set `level.tod_diag` false.
    - Today (2026-10-05) that finds ABFX_C, AMB, BREACHER, CLS_TERM, DEALER, DOPPEL, EYES_C, FALL, GOLDEN, HOUSE, JT, JUMPPAD, LIGHTSTATE, LUCKY, SHOP, SKY, SWORD_C, TELEM, TP_STATE, VEIL, WAR, WAR_SKY and WS (the Wunderstrahl, 2026-10-06). Also zero `TOD_JT_TRACE_UP/DOWN_SECS`.
    - Only DEALER/HOUSE are refused by `-Publish`.
    - The grep misses `_tod_partners.gsc::log()`, which has NO gate at all (left over from bring-up). Restore its `if ( !IS_TRUE( level.tod_dev ) ) return;`.
  - Before a PUBLIC upload, CREDITS.md must credit Nikolai (Ammo Box V6, the TOWER OF DOOM / CYBERCITY sign, the GRID TERMINAL) and the Cyber Teddy's author / Meshy plan (docs/208). Neither entry exists yet.
- **Patch notes / ledger:**
  - `docs/publish_ledger.json` (`steam_item` 3788921059, rows 1-43), `docs/68_patch_notes.md` and the BBCode file are MAP ONE's inherited history. Row #43 is Map One's v19.22, still PENDING.
  - Never close a Map One row, never re-stage #43 as a Tower II release, and never ship notes from today's window (280 entries since Map One's v19.17).
  - Tower II has no Workshop item (`patch_notes.js` `STEAM_ITEM = ''`; its fetch refuses), so `uploaded` always takes `--at`. Read the time off the Workshop page, which shows the viewer's timezone (Eastern here). The durable "Pacific, +3 h" line is wrong.
  - Before Tower II's first `-Publish` (its gate runs `patch_notes.js check`), ask the user how to start Tower II's own ledger and Workshop item.
  - A published promise that stops being true is retracted in the next notes.
- **Special re-reviews:** any change to the floor-20 hall's solids or to `source_data/tod_surface.gdt` needs a Dealer-panel re-review (`tools/dealer_presence/`): update `inventory.js`, render a studio preview (pass the FULL path), add a `rereviews` entry, then stop the studio.
- **Files a receipt pins** (e.g. `tools/sky3d/cyber_architecture.py`):
  - Never put unrendered work in them. Stage it in the pass's own pipeline, then publish one complete reviewed source/art/receipt set.
  - Never unblock a build by rewriting a receipt or adding a gate exception.
  - The v13 sky-depth candidate (docs/166 s15) lives only in `tools/sky_depth/staged_sources/`, unrendered and unbuilt. Never copy it over the live file.

### Verification
- **Freshness:** run the durable diff + `-newermt` pair against `usermaps/zm_tod2_cybercity`. Also list REPO files edited after your build started: the sync preserves mtimes, so a peer's later deploy looks clean.
- **Prove a feature is in a .ff** with four checks:
  - Its ledger rows: csv `index,type,name`, LODs listed lowest detail first; check the `english` ledger too.
  - Its bank stems.
  - Deployed = repo.
  - Nothing synced after the .ff.

  .ff bytes never match between builds, so compare ledgers.
- **A clean link shows only the 3 known-waived lines** (since 2026-10-05: `gfx_teleport_tube_em_scroll_nocull`, `mtl_glass`, `p7_zm_zod_fuse`).
  - Red linker lines do not fail the build: read `tmp/native_build/linker_last.log` for `mismatched usage` / `doesn't expose` / `no techset`.
  - A material row that holds only its name (~41-49 B) is an EMPTY material.
  - A count short by one is a bug.
- **A link is not a boot:** read the console for SCRIPTERROR / unresolved external / Com_ERROR.
  - Lints are static evidence.
  - A test that mocks an engine API cannot prove the API exists, and a mock is not native playback.
  - A Blender render is not the in-game look.
  - A .ff that failed validation, or a wrapper that exited without its audit, is not a build.
- **Logs:** archive `console_mp.log` the moment a user run ends, and check its `Loading fastfile` line (Map One also loads as `zm_tower_of_doom`). Read every user log for every open issue without being asked.
- **Logs while dev is OFF:** a log gated on `level.tod_dev` prints NOTHING in the user's run. For a user test:
  - Gate the log on its own `#define TOD_<FEATURE>_LOG 1`.
  - Build the string outside `/# #/` and keep `PrintLn` inside it (PLAY_NORMAL.bat passes `developer 1` + `scr_mod_enable_devblock 1`).
  - Set the define back to 0 before publish.

  This overrides the durable line that says to gate logs on `IS_TRUE( level.tod_dev )` with no extra toggle.
- **Logs without dev mode, the newer lane** (2026-10-04, docs/210): `level.tod_diag = true` (entry script) lets console-only feature loggers print with `tod_dev` off. Gate a new logger on `( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) )`; never put an on-screen print, a harness or a value behind `tod_diag`.
- **Gates:** when a gate fails a change you believe in, read what it protects and update its contract. Never edit a baseline to make it pass. Keep the old behaviour as a negative-control fixture.
- **gsc_eval:**
  - It has no `switch` (use `||` chains), case-folds locals, and cannot parse `[[ ]]` (use a stub or `__ptrcall`).
  - Functions a gate runs contain no `wait` or `endon`.
  - Every new callee needs a stub (e.g. in `tools/teleporter/test_states.js`).
- **`test_tod_native_api.js`** accepts only call shapes that stock code already uses (LuiNotifyEvent carries 1-5 or 7 values).
- **Lua mocks** must return what the engine returns (`ListHelper_SetupDataSource` returns a TABLE). After a refactor, re-check that the harnesses still model the live fields. On the card-pull mock, never name a field `set*`.
- **Judge visuals** on 1:1 crops and simulated in-game views, and MEASURE colours. Never judge HDR glare on preview PNGs.

### GSC / CSC
- **Directive order:**
  - `#using` comes before every `#insert`/`#precache`/`#define`/`#namespace`.
  - An `#insert` that defines functions goes AFTER `#namespace`; otherwise it fails only when the map loads.
  - Wrap a ternary used as an argument whole: `f( ( c ? a : b ) )`.
  - `lint_tod_gsc_strict.js` runs first.
- **Locals are case-insensitive** (`d` == `D`). Guard with `isdefined` before comparing. Party size settles at `all_players_connected`.
- **Server FX:**
  - Only `PlayFXOnTag` on a `tag_origin` carrier; never bare `PlayFX`, never on an actor.
  - Server `StopFXOnTag`/`LoadFX` do not resolve, so delete the host instead.
  - Hosts delete themselves via a failsafe. Let a fresh host replicate for 2 frames before a one-shot.
  - Thread `tod_teleport::fx_burst`; never call it inline.
- **Sound:** never `PlaySoundAtPosition`: on the server custom aliases play silent, and in CSC it fails the load. Never `zm_utility::play_sound_at_pos` with a name stock never `add_sound`ed: it takes a `level.zombie_sounds` KEY and plays nothing for any other (every door slide was silent until 2026-10-05). Use a script_origin `PlaySound` (`tod_perk_scatter::play_sound_at_origin`) or the entity's `PlaySound( localClientNum, alias )`.
- **CSC timing and clientfields:** CSC `wait`/`MoveTo` count frames, so use `waitrealtime` + `GetRealTime`. `util::clientNotify` sets a state, so space beats at least 0.1 s apart. Register clientfields in the system's `__init__`, an event field before its counter.
- **Movement:**
  - A `SetVelocity` with upward z on a grounded player is discarded, so lift them 1 unit first (`floor_release`).
  - Never `FreezeControls` during a scripted-velocity move.
  - Use one steering lane per flight.
  - A mover carrying a linked player needs segments longer than the snapshot interval (lookahead 2).
  - The first-jump camera is ONE eased path, a pure function of the flight clock (`cine_cam_plan`/`cine_cam_angles`, run by test_jumppad via gsc_eval). Never:
    - Clamp the view on a mover that `RotateTo` also turns.
    - Move the view back the way it came.
    - Turn the view after control returns.

    Turns stay under ~150 deg/s (`TOD_JUMPPAD_CINE_TURN_MAX`).
- **A jump-pad flyer is untouchable** (`player.tod_jumppad_flying`):
  - Spared stock's out-of-playable kill and ALL damage (the pad's callback runs FIRST).
  - Never targeted (ignoreme), never a spawn/elite/ambush/stray anchor, never recalled.
  - The Black Market, the class terminal and every ability refuse mid-flight.
  - Every new target filter, spawn anchor, teleport, damage lane or movement ability must refuse a flyer too.
- **Projectiles/bodies:**
  - A missile deleted at impact has no origin, so track its position.
  - Bows raise `missile_fire`.
  - Ragdolls are client-only, so score flung bodies from the computed arc.
  - A trace on the death frame starts inside the body: wait a frame and ignore the body (`end == from` means it started inside).
- **Actors:**
  - `Hide()` stops an actor's movement/FX; use `HidePart("j_mainroot")` + `ai::gun_remove()`.
  - Partner damage comes from a non-AI gun source without `allow_zombie_to_target_ai`.
  - Never use `level.ai_robot`.
  - Pin `variant_type` after `init_zombie_run_cycle`.
  - Use per-actor hooks (`tod_hunt_filter`, `tod_reloc_fn`), never globals.
  - A Raz-family elite's `favoriteenemy` is rewritten by the stock target service whenever a companion is out (`allow_zombie_to_target_ai`), so the Mangler keeps its own pick in `tod_hunt_player` (2026-10-05: its attack loop skipped the cannon while it held the companion).
  - Never re-play a scripted clip to hold a pose: a play re-places the actor at its align point (the Necromancer's bind dropped the lifted zombie to the floor). Slow the running clip instead (`bind_hold_keep`, UNPLAYED).
  - Every enemy target filter skips cloaked players.
- **Damage:**
  - A `DoDamage` computed from enemy health sets `tod_ps_exempt` and clears it after (nuke idiom `health + 666`).
  - Fallback damage paths consume and clear the same-frame stamp.
  - Derived hits skip attacker multipliers.
  - New kill payouts go through `level.tod_haven_kill_pay_fn` + `kill_preview`.
  - `specialty_sprintfire` has one owner, `apply_sprint_fire`.
  - Another class's card stays dormant (`class_live_level`).
- **Spawning:**
  - Never spawn or relocate where `tod_reach::can_reach` fails, or inside a SAFE haven field (`level.tod_haven_inside_fn`, as `_tod_stray` and `_tod_ambush::legal` do).
  - A new spawn rule also goes in `tod_ambush::legal`, and must honour `tod_house::in_house/in_parlour`.
  - Polling misses same-frame pulses, so latch at the writer (`tod_elite_pause_pending`).
- **Structure:**
  - Never add functions to vendored stock namespaces (`zm_score::`); use public hooks.
  - `_tod_ambush` imports leaf modules only.
  - No ability-fx hooks inside `gs_dive_*`.
  - Never type a generated coordinate into GSC (door/breather/haven/crown/arena/house data).
- **Sky fleet:** one MoveTo + RotateTo per 0.1 s tick; no allocation or log per tick; every spawn counted against `TOD_SKY_ENT_MAX`. The pop guard samples every path.

### Lua UI
- **A new LUI menu is FOUR pieces:** the Lua (`function LUI.createMenu.<name>`), the zone `rawfile` line, `LuiLoad( "ui.uieditor.menus.hud.<name>" )` in `zm_tod2_cybercity.csc`, and the GSC `#precache( "lui_menu", "<name>" )`. Without the LuiLoad, `OpenLUIMenu` still returns a handle and the file never runs (telemetry probe revs 1-3, 2026-10-05).
- **`TodPromptCard.lua`** owns every prompt card: add to it, never back into a card. Zone required rawfiles in the `.zone`, never a zpkg (an unzoned `require` fails silently).
- **Quick Revive's card is STATIC and states both prices** ("SOLO $500" / "CO-OP $1500", `PromptPerks.lua`). Never add a UI-side party or price guess. The charge itself is `_tod_perk_lights::solo_qr_price_fix`, decided after `all_players_connected`.
- **Typeface:**
  - It silently deletes characters it cannot draw and upper-cases everything. `+` and `/` exist only in the digit set, so route them.
  - A price is one glyph row. `TodPromptCard.ICONS` order is load-bearing.
  - The footer key is ONE UIText with `[{+activate}]`; never write a key name into a prompt.
  - Place rows by measuring the chassis art (4 px per unit). Rows on one line share one measured cap.
  - Re-slice with `slice_hud_sheets.js --src .../_sheets`; never hand-edit `TodGlyphMetrics.lua`.
- **Binds:**
  - `Engine.Localize` returns byte 21 + the UNEXPANDED token + byte 20; UIText expands it later. Never trim it or read a key out of it.
  - Card panels and class select choose glyph vs keycap with `CoD.TodKeycap.PadDevice()` (the d-pad latch OR an `IsPadGlyph` expansion). tod_upgrade.lua keeps a local copy of that test; keep both in step. Pad expansions are icons and are never drawn in a keycap.
  - The ability-tile key badge (AetheriumLoadout `TutKey`) reads the device with `Engine.LastInput_Gamepad`, refreshed on `LastInput`.
    - On keyboard, the key name comes from `GetKeyBindingLocalizedString(controller, cmd, 0, false, false)`, trimmed at " OR " and drawn in our typeface.
    - On a pad, or for any glyph that `measure()` returns -1 for, it passes the whole token to engine-font UIText.
- **Lifetimes:**
  - Every owner closes every child (`TodUIOwnership` installed before feature close hooks; `test_ui_lifetimes.lua`).
  - Subscribe LAST, after the slots exist.
  - Module-level values are `local`. No `ipairs` over literals that can hold nil.
  - Respect the 60-upvalue cap (use one layout table). PlayerInfo is at its closure limit: replace calls, don't add them.
  - No `PrintInfo`/telemetry.
- **The clientuimodel pool is FULL (61/61 bits):** new HUD state goes through eventstrings. An eventstring reaches only HUDs that are alive when it fires, so:
  - Re-send the current state to every player on a 2-5 s heartbeat, for late joiners and recreated HUDs.
  - Make a same-state re-send draw nothing.
  - Key party rows by the actual clientNum.
- **Screens:**
  - Full-screen moments hide the HUD via `CoD.TodHudVeil.Set(key,on)`.
  - A card deal takes the screen; anything that reopens the class panel gives way to it.
  - Never show an option the server would refuse.
  - A `tod_jump_cine` letterbox scene longer than 17 s (`TodJumpCine.lua WATCHDOG_MS`) must re-arm the watchdog with the `3` beat every `TOD_HOUSE_CINE_KEEP_SECS` (8 s), as `_tod_house` does. Otherwise the bars and veil drop mid-scene.
  - TodPull's under layer (`AttachUnder`) draws BEHIND the opaque cards, so anything that must show over a card goes in the slot's OVER layer. The LEGENDARY motes after the flip are still hidden there; fixing that is the card owner's call.
- **Values that must match / limits:**
  - `TOD_UPG_PLATE_MAX` = `PAUSE_PLATE_MAX` (63).
  - No non-card image name ends in `_dark`.
  - Text-only cards track `card.imgLive`.
  - Gun icons key on display names (`TOD_NAME_CAT`).
  - Loop animations use `transition_complete_*` (not UITimer); tints go on a parent element.
- **Previews:** `tools/ui_mockup/render_menus.py --check` (a gate), `render_spin.py`, `render_pull.py`.

### Assets / GDT / linker
- **GDT format:**
  - No `//` line anywhere, inside braces too; the file starts with a brace.
  - One asset per name AND type across all GDTs (`tools/lint_tod_gdt.js`).
  - No Blender `.001` suffixes.
  - Material names <= 63 characters; longer ones are silently replaced by a default.
  - FX paths <= 63 characters (`lint_tod_fx_paths.js`; child effects are named `<parent>_c<N>`).
  - Every authored material needs an explicit valid `surfaceType` (e.g. `metal`, `flesh`). The linker refuses a material without one and aborts the whole link, and no gate checks new ones.
- **Images:**
  - Compressed images are multiples of 4 in both dimensions. Images whose sizes are not powers of two need `noMipMaps` + `noPicMip`.
  - Diffuse = `compressed high color` / `sRGB3chAlpha`.
  - Give a texture the usage its slot's techset reads (`SLOT_USAGE`), not the one its filename suffix suggests. A transparent scalar-mask techset needs a scalar `specularMask`.
  - Zero `missing_techsetdef` rows.
  - UI art whose sizes divide by 4 goes `compressed high color`, to save resident RAM.
- **Zone lines:** never zone a bare material that an xmodel uses (zone the xmodel). Brush/chalk face materials ride in with the BSP (no zone line).
- **AI animation:** selector rows dictate loop flags (move: `looping 1` + `loopsync 1`; idle/melee: both 0). Every scripted `%anim` belongs in its `.ai_am`. AI tables are CRLF.
- **Models:**
  - Derived xmodels ship `japaneseUnsafe 0`.
  - The converter drops zero-area and needle triangles, so compare compiled vs exported triangles on every LOD and read the `share/assetconvert/xmesh/v6/` logs.
  - Preserve mesh objects (a flat PyCoD load can drop one).
- **Installers:** subtract their own GDT's assets from stock lookups; prefix imported textures (`i_tod_jp_*`); never hand-edit generated GDTs.
- **Weapons:**
  - **Registration count.** `LEDGER_GUARD` 235 in `gen_tod_twins.js` throws only above 235 (the build log prints `REGISTRATION LEDGER`), so check the count yourself.
    - Known to boot: 229 (this map) and 235 (TOD1, 2026-09-09).
    - 368 crashes at boot; 236-367 are untested.
    - Pay for any new registration by retiring weapon forms (QUICK DRAW was paid for by retiring the blades' k1/k3).
  - Card-driven twin axes exist (bows `d`/`s`, Breacher `e`). Every form counts against that ceiling.
  - The weapon COST table is a separate client registry (`SetWeaponCosts`; overflow shows "Too many weapon costs" at connect). Keep it at 240 base/up keys or fewer; `verify_weapon_costs.js` gates it.
  - Archer and Breacher primaries are pinned to `TIER_SUSTAINED`: ACC's gun-class mean sustained DPS per tier. Bows count their minimum draw, and no gun hits harder at range. Warrior blades keep ACC's Slasher lead (the user's call). The Necromancer's weapons deal script damage.
  - A `sharedweaponsounds` block's `meleeEntityImpact*` fields name an `entitysoundimpacts` ASSET and `meleeSurfaceSound*` a `surfacesounddef` ASSET, never an alias (the linker refuses it). Define those assets pointing at the aliases, as `tod_punch_hits_*` / `tod_punch_surfaces_*` do.
  - A thrown charge is `plantable 0`. A lethal offhand needs `ammoCounterIcon`. On segmented reloads, `reloadAmmoAdd` = `clipSize`.
  - For a Single Shot weapon, `fireTime` sets both the fire rate and the weapon-switch pause. `DisableWeaponFire` gates only Charge Shot.
  - **The Archer's bows release themselves at full draw** (`chargeShotFireWhenQueueReachesMax 1`, docs/218_archer_auto_bow.md; `holdFireTime` = `chargeShotMaxTime`). A held arrow is the attack button still DOWN at `weapon_fired` (x3); the DPS pin counts the HELD full draw (`AUTO_DRAW_FULL_MULT`, LOCKSTEP `TOD_AB_MAX_MULT`). `guidedMissileType None` = flat flight.
  - `meleeAltAnim` is ignored (use LEFT twins). Move `tag_flash` by editing the clips. Packed forms carry no optics.
- **Retire things whole** (domain + slug + zone lines; weapon + aliases + every script path that used it), and never delete on a name-grep alone.
- **Materials suspected of compiling empty:** `mtl_wpn_t7_c4_decal2`, `sat_zm_machine_y_mod_01_on`, the Fire Bow rune crystals/orb, the 115-grenade set.
- **Donors:** Hellbound GDT snapshots live in `donor_gdt/hellbound/`; clones emit `cc_*` stems (`hbPreflight`).

### Sound
- **Before playing an alias:** confirm that a CSV we ship defines it and that its stem is in the loaded bank. Aliases in the base fastfile cannot be tuned. Clear sound contexts we never set (`lint_tod_sound_context.js`).
- **Weapon/anim sound:**
  - Xanim sound must be a "2D Sound" custom note; baked notetrack names are silent.
  - Weapon GDT sound fields that name unzoned aliases are silent.
  - Fire aliases are never Pauseable.
  - Native notes own the timing, never script sleeps.
- **Loops/music:** never use a looping 2D alias you cannot stop. Stoppable music = a looping 2D streamed alias on the music channel. `_tod_atmosphere` owns that channel. Music is `snp_never_duck`, so cues must be loud on their own.
- **Music mastering:** `tools/music_master.py` is the one recipe. Measure by band RMS (`tools/music_measure.sh`), re-check peaks after EQ, and put the limiter after a resample. Legitimate sources only (lossless upgrades need the user's purchases).
- **Generated sound:**
  - Read the key only from `ELEVENLABS_API_KEY` and never print it.
  - ElevenLabs puts the loudest moment first, so reverse rising cues. Measure and level takes via `make_sounds.py`.
  - Dealer lines ship only through `pick.py` (mask applied). Voice desks stay LOCAL.
  - Generated alias CSVs are never hand-edited.

### FX
- **Stubs:** before zoning a stock effect, grep it for `gfx_debug_missing_fx`. Known stubs:
  - `fx_elec_burst_lg_z270_os` (use `dlc1/castle/fx_elec_teleport_flash_lg`)
  - `fx_dog_fire_trail_zmb`, `fx_embers_falling_sm`, `fx_ash_embers_light`, `fx_fire_debris_xsmall`, `fx_blood_torso_explo_zmb`
- **The 1p rule:** nothing big or bright spawns at the shooter's camera (no flash, flare, dynamic light or puff). When an effect is "in the face", first read where the script SPAWNS it.
- **Ability routing:**
  - World one-shot -> `burst_at`.
  - Zombie -> `actor_hit`.
  - Player -> a kind on `play()` with 1p + body halves (body one-shots play for other players only).
- **Effect authoring:**
  - Sprites are billboards, so on round surfaces place rings of beads on the sphere (`FLAT_MAX` 48).
  - Count overlapping particles before choosing alpha.
  - Strip MESH elements from projectile effects. `.efx` children also live in `attachment`.
  - Effects cannot scale.
- **Server one-shot effects render nothing:** use a looping FX on a host and put any pulse in the light curve. A loop played on a tag cannot be stopped with `StopFX`; delete the host and make a new one.
- **Lights:**
  - Copy the perk-glow `dynamicLight2` (hue on `colorGraph`, white def, one light).
  - Haven lights must pass the validator: r <= 400, shadowless, all four states, at most 2 alive.
  - Substantial FX follow `docs/155_fx_art_workflow.md`.

### Models / materials (beyond the durable checklist)
- **Material quirks:**
  - Vertigo-pack materials are polished mirrors; doors use the matte `tod_door_<hue>` clones.
  - A BO6 port that looks dead is missing its emission sheets.
  - An ON state is a `skinOverride` `_on` twin swapped in with `SetModel`.
  - `colorTint` is not honoured on character materials, so bake the colour into the texture.
- **Export rules:**
  - Boolean-cut faces lose custom normals: use the geometric fallback + the unit-normal gate.
  - Preserve connected parts in LODs.
  - Collection names <= 63 chars; unhide objects before export; compare `armature.bones` as sets; PyCoD models need an explicit version.
- **Rigs:**
  - Never rotate a staff rig whole.
  - Player clips do not fit the Keeper/Dealer skeleton. Keeper weapon tags are loose, so derive palms from the wrists.
  - Route direction flips through a waypoint.
  - Decode `xmodel_bin` for pivots and bounds before placing a prop.

### Geometry / navmesh
- **The `.map` is GENERATED** (`node tools/gen_tower_map.js`) from its tables and layout sources: `haven_layout.js`, `tower_transit_layout.js`, `battle_arena_layout.js`, `dealer_house_layout.js`, `broken_tower_layout.js`. Each source checks its own layout on load. Anchors are emitted to the `_tod_*_data.gsc` files.
- **Navmesh:** Havok gives no polygon to a terrace that can be climbed from every side, so build open-sided flights bordered by drops. Prove a new room with cod2map on a scratch map + `tools/lint_tod_navmesh.js <hkt>`. Every detached region needs a seed, its own `ISLANDS` entry, and anchors in the navmesh lint.
- **`lint_tod_geometry`:**
  - Teach it every new non-axial/sloped label; it skips labels it does not know.
  - `_tinted` and `tod_cc_ruby` read as DECK, so use plain hues on thin trims.
  - A raised top is a slab 64 units or shorter, and a stair foot lands on open floor.
  - Redirect new generator outputs in `lint_tod_geometry_parity.js`.
- **Triggers/props:**
  - A trigger origin is never inside a solid (the generators throw).
  - Free-standing props get `steepCap`.
  - Nothing stands on the causeway/balcony deck (assert 5f.9).
  - Re-measure the jump-pad shell wedges (`JP_SHELL_*`) on any model change.
  - Crown rooms stay inside `JP_CRN_BOX`.
- **Doors/rooms:**
  - A clip that must vanish with a door rides in the door's slab entity.
  - Nothing rotates in the `.map` (use script_models).
  - Split walls need lintels.
  - Every pocket gets a riser, and sealed-fight spawn boxes exclude surfaces outside the seal.
- **Arena:**
  - A ledge must sit no more than 256 above arena floor.
  - The roof vent is a 24-unit slot.
  - Keep `battle arena floor` at its v1 extent.
  - No zombie traversal links.
- **Placement constraints:**
  - Floor signs go where the player ARRIVES.
  - Floor numbers are on the paid doors only (user 2026-10-05: "I only want it on the door"). Never put them back on the rails.
  - Keep haven solids off conduit inlay patches.
  - `SKY_TOP` never goes below `SUN_VOLUME_TOP_MIN` (39,468).
  - War props respect the keep-out zones.

### Sky / lighting
- **Read `docs/162_lighting/README.md` first.**
  - `set_lighting_state(n)` shows Radiant State n+1; the map boots in State 2.
  - Power-gated lights are `lightingstate1`-only.
  - The sun volume needs ssi2/ssi3 + `tod_sun_probe_target`.
  - Each filled lighting state roughly doubles the LED.
- **Sky bearing:** the image centre faces yaw `-(SSI sun az + skyRotation) - roll`. MEASURE it (`tools/sky3d/screenshot_fit/`), never predict it. Values that must match: `TOD_JUMPPAD_CINE_SIGN_YAW` with the sky, and `TOD_WAR_SKY_SIGN_YAW` = `TOD_JT_SIGN_YAW`.
- **Sky-fleet lanes:** after any `.map` geometry change, any black-hole move in `build_city.py`, or any skyRotation/SSI sun change, run `node tools/sky_ships/gen_lanes.js`; otherwise its `--check` gate fails.
- **Brightness:**
  - `skyStops` scales the VISIBLE sky; never cut it to "hold the world light".
  - `SKY_INTENSITY_FACTOR` is 10 in the generator, but its effect above 1 is UNVERIFIED (no stock map uses more than 1). Move the visible sky with `skyStops`.
  - SSI EV is the exposure lever.
  - Keep the fixed sky gain; do not re-solve it, which brightens the foreground.
  - Update `SKY_STOPS`/`SKY_SCORE` in `tools/art_cohesion/verify_tower_design.js` in the same edit as any change.
- **Sky limits:**
  - 8192x4096 is the ceiling: the converter refuses 16384 ("unsupported size") and the FULL build fails.
  - A sky change is a FULL build.
  - The sky is excluded from the texture size pass.
  - Bake the sign dark and overlay the lit version (the `tod_jt_sign_lit` card; `scaleRGB` 16 is its one brightness knob).
- **Probes:** a fitted near-cubic probe costs ~28.5 MB of LED; growing probe boxes is the user's call.
- **Fog:** the night fsi fogs the skybox at 65,000 units. Change fog with a `set_fog` lerp that only writes on change, never by switching it off. `fog_off()` must use `TOD_FOG_OFF_*`: zero or equal values divide by zero and give a black screen.

### Art pipeline
- **Self-serve flow** (`tools/artgen/README.md`): brief -> generator -> review by a SEPARATE agent -> land in one step -> one FULL build. Output is deterministic with a `--check` gate, uses our typeface for every letter, and matches the shipped neighbours. The zip (`tools/make_art_pack.ps1`, durable section) is the fallback.
- **One library** (user 2026-10-05: "Whole entire asset library should look like one library"): every new image joins a family in `tools/artgen/README.md` "THE ONE LIBRARY" and is drawn by (or through the helpers of) that family's generator. A picture of a weapon shows the one `register_gun` / the weapon GDT's `gunModel` hands out, rendered from its model (`r2` / `r5`), never drawn from memory.
- **Generated, never hand-edited:**
  - `gen_hpbar_art.js`, `make_gift_art.py`, `make_badge.py`
  - `dealer_house/make_spin_art.py`
  - `jump_title/make_sign_card.py` / `gen_fx.py`
  - `haven/make_dome.py` / `make_fx.py`
  - `war_damage/*`
  - `card_pull/install_card_art.py`
  - `floor_numbers/make_assets.py`
  - `typeface/typeface.py` (`--pin` only for a deliberate redraw)
  - Every installer.
  - The 2026-10-04/05 asset waves: `artgen/packs/*` (pk01..pk09, r1..r6, `r10_card_chrome.py`, `w2g_companion_plate.py`, `w3b_ability_colour.py`, `w3c_class_pack.py`, `w3f_library.py`), `wording/wording_pass.py`, `companion_maps/compose.py`, `dealer_fx/gen_fx.py`, `dealer_sfx/make_sounds.py`, `sfx/w2c_sounds/*`, `fxgen/elites/*`, `original_rips/make_original_rips.py`. Each has a `--check` in build_map.ps1.
- **Blender MCP studios** each own a port: 9876 sword, 9877 cyber zombies, 9878 altar, 9879 teleporter, 9881 Black Market, 9883 crown colour/wires, 9887 alarm button, 9888 lucky, 9890 sky fleet, 9899 Dealer.
  - Keep the window visible for the user.
  - Edit the shop and the Dealer on STAGED copies and swap them in whole.
  - Keep editable masters; ship baked derivatives.
- **Sky renders:**
  - Author the sky only through its pipeline: `tools/sky_consistency/` and `tools/sky_middle_ground/` (MCP author/finalize scripts + `install.py`). They write the editable master `art/sky3d/tod2_sky.blend`, whose hash the receipts record. Never hand-patch it or a receipt outside the pipeline.
  - Fog is a mesh box.
  - Author lights in W (minor channels <= 0.05 W). `bpy` byte pixels are display values.
  - Use `soft_fan()`, not cones, for plumes. Cap shader lines to a fraction of a cell.
  - Reopen previews via `open_preview.ps1`.
- **The Art Atlas** (user 2026-10-04): https://claude.ai/artifact/4asJNWDJnvJYrivKW89YfE is the user's browsable gallery of every image the map ships. After ANY image lands, changes or retires, run `python tools/art_gallery/build_gallery.py` and republish to that same URL (`tools/art_gallery/README.md`).
- **References and drops:**
  - Copy user references BY MEASUREMENT.
  - Park replaced art in `docs/<NN>_ref/_prev_shipped*/`.
  - Verify installed art by hash against the drop.
  - An art install is not done until you have read its draw path: a disabled flag hides packed art.

## THE QUALITY BAR: AAA, BUG-FREE, FUN FIRST (user, 2026-09-29)

User: *"all features we build are buggless production ready with Triple AAA
implementation and visuals, sfx, and animation are always considered to provide
the best player experience and fun will be prioritized."*

**Every feature ships bug-free, production-ready and built to a AAA standard.
Visuals, sound and animation are part of every feature, never an afterthought.
The best player experience decides every call, and fun comes first.**

What that means in practice:
1. **Design the experience first.** Write down what the player sees, hears and
   feels, moment by moment, before choosing the technique. Never shrink the
   design to fit the easiest implementation; find the technique that delivers it
   (user 2026-09-28: *"think of the experience first ... I dont want to limit
   ourselves"*).
2. **Visuals, sound and animation, every time.** Every player action gets
   feedback you can see and hear. Every state has a clear look: ready, busy,
   refused, done. Flat boxes and plain text are a placeholder, not a finish: if
   the art or sound does not exist, request it (an art pack, a sound brief) in the
   same pass and wire it in when it lands.
3. **No half-finished handovers.** Done means built, gated, logged and reviewed,
   never "the core works, polish later". Handle every exit path: cancel, timeout,
   down, death, disconnect, pause, a card deal mid-action, co-op.
4. **Review for bad player experiences before calling anything done.** Walk the
   whole flow as a player and fix: HUD clutter behind a full-screen moment, prompts
   over menus, text that does not fit its box, unclear wording, missing or harsh
   sounds, accidental inputs, stuck or soft-locked states, damage the instant
   control returns, co-op collisions, and anything slow, confusing or bland.
5. **Prove it, and say what is proven.** Automated gates for the logic, dev-mode
   logs for the playtest (see "Dev-mode diagnostics for feature work"), then the
   user's playtest. Report plainly what is verified and what is not.

### Model surfaces: believable materials and wear (user, 2026-09-29)

**Every model we create or revise must have finished, realistic surfaces that
belong beside Black Ops III's native assets. A uniformly clean, flat-color skin
is a placeholder, not a completed model.** This applies to ships, asteroids,
weapons, machines, alarms, buttons and other props from the first art pass.
The user must not need to request the missing surface detail again.

**Sky consistency correction (user, 2026-09-30):** the approved close buildings
set the architectural/material family for the entire skyline. Near, middle and
far buildings share construction, panel scale, coating/alloy finishes, purposeful
wear and inset lighting. Simplify distant detail without switching to another
building kit. Keep major towers' recognizable silhouettes and the title's scale
and menace, while matching their materials. Planets, moons, rings and stars need
surface contrast and restrained halos; bright emissions must not erase their
detail. Preserve the established foreground brightness when reducing celestial
radiance: a whole-sky gain solve must not silently brighten everything else.
Review the full panorama and matched near/far/title/celestial views before building.

**Dealer identity (user, 2026-09-30):** the title crest must resemble the
existing Black Market dealer: black hood, angular charcoal mask, red X eyes
and uneven stitched red grin. Preserve the accepted imposing cyber sign and
its dull-before-jump / bright-after-crash states. Repeat the same character
sparingly across the playable route. The Dealer is the chosen **final boss**,
not the Battle Arena Keeper; a role/design decision is not a shipped fight.
Do not swap the rigid shop prop onto an AI rig or silently reactivate the
parked Crown finale. Canonical references and implementation boundaries:
`docs/dealer_identity.md`; proposed encounter: `docs/dealer_finale_design.md`.
Current voice direction is docs/198 round two: calm, occasionally manic.

**Shared workstation memory (2026-09-30):** this PC has 16 GB RAM. Heavy
Blender exports/denoising must not overlap a Radiant bake, including another
map's process. Match `Radiant*` (the actual executable is
`Radiant_modtools.exe`), not just `radiant.exe`; also wait for `cod2map64`,
`linker_modtools` and `gdtdb` so Blender cannot start between bake stages.
Check before launch and during long production renders; if a native stage
starts, stop only the render owned by that wrapper and keep its logs.
Never close another map's process or its dialogs. Also retain the BlackOps3
guard. Small source edits/read-only
diagnostics can continue while rendering waits. A successful Blender render
does not establish that overlapping workstation load was harmless.

- **Choose the material before the damage.** Painted steel, exposed alloy,
  brass/copper, rubber, glass and rock need different color, normal and
  gloss/specular responses. Reuse the material language in
  `docs/art_cohesion/README.md`; hero props may keep their own atlases.
  Roughness in the authoring scene must translate into the actual BO3 material
  and gloss maps, not a studio-only shader override.
  Transparent covers must reveal their intended internal mechanism in both
  lit and unlit states. Keep overlapping glass layers and atlas padding from
  accumulating opacity. Verify the actual compiled alpha/mips and packed
  shader's specular mask/tint; a Blender-only glass shader or an unrelated
  shader variant is not proof. Match the image semantic required by the actual
  techset (a scalar linear `specularMask` differs from a full-color
  `specularMap`). A dependency/ledger name can still represent an empty material:
  require a complete native definition and real texture table after linking.
  Alarm reference: `docs/crown_alarm/GLASS_REPAIR.md`.
- **Place small imperfections where they make sense.** Use restrained coating
  wear on exposed edges and hand-contact areas, dirt in joints/recesses,
  fastener seating and contact occlusion, machining grain, small scratches,
  chips and dents. Add oxidation only to susceptible materials and locations;
  put heat staining/soot near working exhausts. Rock needs irregular mineral
  variation, fractures, pits and granular relief. Avoid uniform noise, evenly
  scratched panels, or rust over every surface. Retain quieter areas so the
  construction and silhouette stay readable.
- **Detail at several scales.** Broad material/panel variation establishes the
  object at play distance; medium seams, fittings and wear explain its assembly;
  fine normal/gloss detail rewards a close view. Choose texture density and LODs
  from the actual viewing distances. Tiny detail must survive mipmaps without
  shimmering; more polygons or larger textures alone do not establish quality.
- **Let the material catch light.** Use real bevels/normal relief, deliberate
  specular and gloss variation, and subtle contact shading. Preserve highlights;
  an all-matte finish flattens surfaces too. Do not bake a studio's directional
  shadows or highlights into albedo, or hide missing surfaces under emission,
  bloom, contrast, darkness or a universal grunge overlay. Keep glow localized
  to the device's intended luminous parts and preserve its existing state tells.
- **Ship the detail, not just the preview.** Preserve editable Blender MCP
  masters and reproducible bake/export sources. Check native UVs, maps, material
  bindings, normals and every LOD; inspect the exported model under matched
  lighting, both close up and at ordinary play distance, with bloom disabled as
  well as enabled. Native asset/conversion gates must pass without geometry or
  texture-coverage waivers. Substantial energy/rift/trail work also follows
  `docs/155_fx_art_workflow.md` for authored layers, timing and bounded cost.
- **Keep the evidence honest.** Record what the Blender/export review proves,
  build through the guarded scripts, and stop for the user's playtest. A studio
  render or successful native build does not prove the in-game look, lighting
  or performance. Read the lighting reference before changing glow or lights.

## HOW TO END EVERY RESPONSE (user, 2026-09-04)

**Every response that changed anything ends with a "What changed" block:
super basic, concise, plain language, easy to understand.** Three to six short
bullets at most: what was changed, where it lives (one file or feature name
per bullet, not a path list), and whether it is built / played / still
pending. No engine talk, no version numbers, no reasoning, no history. Write
it for someone who only reads the last five lines. **If the user wants more
detail they will ask** — the full explanation goes ABOVE the block (or in the
CHANGELOG), never inside it. Example:

```
What changed
- Gun HUD icons: audited. Nothing is broken; the set is one picture per KIND of gun, so Stoner and HK21 share one.
- New art request zip in Downloads asking for 20 per-gun icons on one sheet.
- Nothing in the game changes until that art comes back. No build needed.
```

## What this map is (user, 2026-08-17)

- **SPIRAL TOWER, 50 FLOORS — v8** (user 2026-08-20: "4 stairs per floor is
  way too much"): a solid core with an open-air staircase spiralling around
  its OUTSIDE — base arena at the bottom, 50 floors of **2 flights each**
  (`LAP_RISE 384`, top z=19200), rooftop arena (PaP; Mule Kick RETIRED
  2026-08-25) on the core's
  top. PARITY spiral: odd floors climb the E+N sides (NE mid landing, NW end
  landing), even floors the W+S (mirrored); doors/zones/lights/probes all
  parity-mirrored in the generator. 52 zones; buyable doors one per lap + roof
  + power (v10.4: 750 +60/lap cap 3000, roof 7500, power 750 — the price
  rides in the GENERATED `_tod_door_data.gsc`, so a price change is a
  -GscOnly build; the `.map`'s own `zombie_cost` is a dead CONSTANT 1000
  placeholder since v14.14 and must stay constant — see below). The prompt
  shows destination AND price; the price is read live at purchase, so after a
  party-size change the sign can be stale by design.
  **TRIGGERSTRING BUDGET — A STANDING CONSTRAINT, NOT A PAST BUG (v14.14).**
  `SetHintString` mints ONE PERMANENT engine slot per DISTINCT string, cap
  **250 per match**, never freed, shared with stock; overflow fatals with
  `BG_Cache_GetIndexInternal` and **blames whoever registers NEXT**, so the
  reported site is never the cause. The map sits at **140/250**. The Aetherium
  hint pack routes on hint TEXT (`string.find` in every `is*Hint()`), so
  `SetHintString` is its ONLY input channel — every new interactive object with
  a varying prompt spends permanent slots. Two rules paid for in blood:
  (1) **never interpolate a many-valued runtime value into a hint** — a
  re-stamp keyed on party size is fine on ONE trigger (≤4 strings) and fatal
  across 53; (2) **count DISTINCT STRINGS to prove a fix** — v14.3's flatten
  ran too late to do anything and its dev print still reported success, because
  it proved the loop executed rather than that a slot was saved. Free lanes:
  constant strings, `IPrintLnBold`, clientfield → LUI. LUI `SetText` is a
  DIFFERENT cache (cap 2048) and is safe.
  **BOTH RULES ARE NOW MECHANICALLY CHECKED** — `tools/lint_tod_hints.js` runs
  on EVERY build including `-GscOnly` (a reworded hint is exactly the GSC-only
  change that skips every other gate). It counts DISTINCT STRINGS (83
  tod-authored as of v14.58; the 140/250 figure above includes stock's share,
  which no tool here can enumerate) and FAILS on any interpolated hint that has
  not declared how many strings it can mint. `lint_tod_hints_selftest.js` breaks
  the map seven ways and requires a catch on each — it caught the lint itself
  reading `TOD_NOUNS` with a bare `indexOf` that still matched a RENAMED table.
  **CURSOR-HINT ROUTING — WORDING DECIDES WHICH CARD THE PLAYER SEES (v14.58).**
  The kit picks a prompt card by pattern-matching the hint TEXT, so a wording
  choice is a UI choice. It shipped wrong for months: the wall-buy arm was
  `"[Cost:" in the text` AND `getCursorHintImage() ~= ""`, and **that image
  guard never fires** — so every PRICED NON-DOOR interactable (ammo crates, the
  Heavenly Gift Altar, CALL EXTRACTION, every spire buy) drew `PromptWallBuy`
  and its hardcoded description **"Wall Weapon"**. Doors escaped only because
  the door keyword excluded them one line earlier. Two GSC files carried
  confident comments reasoning from that dead guard — *a guard nobody has
  watched fire is not a guard*. The router is now ONE `classifyHint()` returning
  exactly one state, arm order irrelevant; WallBuy/MysteryBox/GobbleGum have no
  arm at all (this map has none of those three). **Every custom prompt must lead
  with a NOUN listed in `TOD_NOUNS`**, which is claimed before any generic
  keyword test — that is what lets the ammo crate say "Pack a Punch $5000"
  without landing on the PaP card. Hint grammar, parsed by `PromptDefault.lua`
  into a title band + two detail lines + price + footer:
  `Hold [btn] ^5<TITLE>^7 - <detail> / <detail 2> ^2[Cost: N]`.
  **THE FOOTER KEY IS ENGINE-RESOLVED (v16.29, 2026-09-02, docs/69).** Every
  `Prompts/*.lua` footer is ONE line, `Hold ^3[{+activate}]^7 <verb>`, set
  through that card's `SetFooter` — the kit's hardcoded literal `"F"` told
  every pad player and every rebinder the wrong key for months. NEVER write a
  key name into a prompt or a menu: the engine expands `[{+bind}]` tokens in
  LUI text (proof: the "HoldX" transcription of v14.58, and every stock hint).
  The pause menu's UPGRADE CARDS legend is the live-bind readout AND the probe
  for bind names other than `+activate`. **The card-panel hint plates draw the
  live binds too since v16.32**: blank frame `i_tod_hint_frame` + token text
  lines (`USE_HINT_FRAME_ART` in both card menus, ONE writer each —
  `ShowSwitchPlate` / `CardHint`); the re-baked keyed plates are the flag-off
  look. **THE COPY IS ONE LANE PER ACTION SINCE v16.84 (docs/88) — DO NOT ADD
  A SECOND.** Three individually-defensible changes (v16.32 split the plate to
  two lines, v16.57 swapped in the offhand pair, both kept a `D-PAD` tail) left
  THREE plates, FOUR lines and SEVEN key names on screen for a two-button
  decision, with LOCK said twice and no line ever saying which card a key moved
  to — user 2026-09-03: *"our last update made it more confusing and less
  simplified by adding so much to look at"*. The plates now read
  `[tac] < SWITCH > [lethal]` and `HOLD [jump] TO LOCK`, and the pause legend
  says the same. **A menu that accepts eight inputs must still ADVERTISE one**
  (stock's "Hold [X] To Buy" never lists alternatives); melee, reload, WASD,
  the stick and the d-pad all still work unadvertised. The offhand pair is the
  one named because it is read ABOVE the station's device gate, so it is the
  only pair correct on every device in every place the panel opens. **AND WHEN
  A LANE IS RETIRED, GREP EVERY READOUT THAT NAMES IT** — the pause legend
  advertised `+attack`/`+speed_throw` for a day after v16.57 removed fire and
  aim as menu inputs, so players pressed fire, saw nothing move, and concluded
  the menu was broken.
  **THE DISPLAYED CONTROL SET IS PAD OR KEYBOARD, NEVER A THIRD (v17.55,
  user 2026-09-04: "the UI should only show dpad options or KBM. Two sets
  only").** Glyph-vs-keycap is chosen by ONE reader,
  `CoD.TodKeycap.PadDevice()` = the d-pad latch OR the `[{+bind}]` expansion,
  which follows the LIVE device. ⚠️ **THAT TEST DID NOT FIRE FOR ITS FIRST
  THREE VERSIONS, because this file and the memory both had the MECHANISM
  wrong** (corrected v18.47, 2026-09-08, from a screenshot): on a pad the
  engine expands a bind into a **BUTTON ICON**, not the letters `LT`, so
  matching on the SPELLING never matched and every pad player got keycaps —
  filled, by the keycap's own text fallback, with the engine's LT / RT / A
  pictures. That is the third set, and pressing the d-pad hid it by latching
  the device a different way, so it survived every playtest. The test is now
  STRUCTURAL — `IsPadGlyph`, any byte outside printable ASCII — which is valid
  on ANY token (the A/B/X/Y ambiguity is a property of NAMES, not icons), so
  the lock plate is covered too. All three surfaces call PadDevice; never
  branch on `CoD.TodPad` directly again. **And the keycap fails closed**:
  `paint` refuses a glyph expansion rather than drawing it as text, in the
  widget AND in each menu's fail-safe stub, because the stub's fallback is
  where the icon actually got in.
  The d-pad latch (`tod_input_pad` / `CoD.TodPad`) is otherwise ONLY the input
  gate — since v16.84 no control string branches on it, so it never decides
  what art or wording is shown. "Detect the
  device at class lock-in" cannot work: jump and use exist on both devices, so
  the d-pad is the only device-proving input the server ever sees. **CORRECTED 2026-09-03 (v16.81): it is NOT a proof — `players/bindings_0.cfg` binds keyboard 1-4 to `+actionslot 1/2/4/3`, so a KBM player tapping 3 or 4 sets `tod_input_pad`; the latch now gates the STATION lanes only and round events keep every lane live for every device. Read `players/bindings_*.cfg` before any claim about what a key does.**
  **NO wallbuys** (user: "I never asked for those").
  **PERKS = the 9-machine random scatter** (`_tod_perk_scatter.gsc`): all 9
  machines (Jugg/Speed/QR/Stamin-Up/Widow's/Death Perception/DoubleTap/PhD/
  WISP TEA — v14.16 2026-08-30: Deadshot RETIRED for the BO7 Wisp Tea, a
  vendored WetEgg module on specialty_nomotionsensor, `_zm_perk_wisp_tea.gsc`)
  park at the base N wall in the .map, scatter to random pads at load and
  reshuffle every 4 rounds (v10.3; was the round after each Panzer), never
  onto the same floor; pads = **the 8 breather pads ONLY**
  (2 per balcony × floors 10/20/30/40) **plus ONE base pad where QUICK REVIVE
  is pinned** (v6.9 solo carve-out:
  **NO PERK LIMIT (2026-09-27, user: "There will be no perk limit on this
  map").** `level.perk_purchase_limit` is **16** in `zm_tod2_cybercity.gsc`,
  one writer, deliberately above the roster so a new machine needs no lockstep
  edit. The PERK SLOTS domain (id 40) is retired WHOLE for the second time
  (v16.80 retired it, v17.3a restored it): no `add_domain`, no
  `level.get_player_perk_purchase_limit` hook, no "PERK SLOTS FULL" line, no
  card images; id 40 stays mapped and its r40 pause plate stays zoned. Count
  `zm_perk_machine` entities in
  `map_source/` for the SIZE, and identify WHICH perk each one is by the
  `model` on the perk-park entity — **NEVER by the specialty string**, which is
  just an engine slot a custom perk got hung on, and which has rotated
  (`specialty_electriccherry` is PhD Flopper, `specialty_combat_efficiency` is
  Death Perception, `specialty_nomotionsensor` is Wisp Tea; and
  `specialty_doubletap2` carries a DIGIT that a `specialty_[a-z_]*` grep
  truncates into the real-but-wrong `specialty_doubletap`). A perk-name grep
  over the `.map` reports PhD and Death Perception ABSENT — all four readings
  wrong. Every prose list of this roster, including the one above, has
  been stale at least once (the user caught a "10 perks" claim on 2026-08-31
  that came from this file naming a retired Mule Kick). the first-breather pin costs 15,750 pts of doors to
  reach (lap 10 under the v9.43 prices), leaving solo with no self-revive for ~10k pts. Granting the perk early
  is NOT an alternative — the stock vending trigger refuses a buy while the
  player holds the perk, `_zm_perks.gsc:545`). 9 pads / 9 machines — every
  pad filled (the "one empty pad" era ended when PhD joined the pool,
  2026-08-25).
  Breathers (floors 10/20/30/40) are **WALLED, OPEN-TOP LOUNGES** (v13
  2026-08-28, docs/42; **the roof was REMOVED in v13.6** — user: "you cant
  look up and see the tower", so the lounge is walls + sky, and an earlier
  version of this line still said "grew ROOF + WALLS" for three days): the
  544×576 deck kept its footprint and grew WALLS (56 sill / open window band
  with glowing mullions, `clip_player` so bullets pass / lintel / a glowing
  cap band on the wall heads), ONE THEME COLOUR each — 10 blue, 20 green, 30
  orange, 40 gold — and the TELEPORTER moved onto its own open-air SPUR (gated
  doorway → 320 gantry → 288×288 floating pad). **v16.7 polish (2026-09-01):**
  a lit `_tinted_edge` panel in the window bay behind EVERY machine (the
  whole perk wall is one), corner finials, a floor inlay ring with a spoke to
  each amenity, pad pylons, two gantry hoops, an under-glow band + pendants
  under the slab, four accent lights, four looping ambient FX per lounge
  (`_tod_atmosphere::lounge_fx`) and a per-player first-arrival chime
  (`tod_lounge_arrive`). All brushwork, zero models; every knob is a `BR_*`
  constant in the generator's v16.7 block.
  **THE AMMO CRATE IS ONE CONTRACT (v17.38, 2026-09-04, user: "master ammo
  crates so we dont ever have to touch them again")**: facing (`CRATE_YAW_*`,
  front = yaw + 90 — the tower crates were authored BACKWARDS until v17.37),
  occupancy (`crateBox()`, the measured box rotated to the real yaw) and the
  trigger (`CRATE_TRIG_OUT` 56 in front, `CRATE_TRIG_R` 72, EMITTED into
  `_tod_breather_data.gsc` and read back by `_tod_ammo_crate::spawn_trigger`)
  all derive from one origin + yaw in the generator, for EVERY crate — base,
  breathers, crown, spire arena/shelves/hubs (94 `ammo crate body` brushes,
  zero script clips). A trigger ON the model origin was the "only at a
  certain angle" bug: an 18u band. Never add a crate any other way.
  Furniture is one-per-wall (station N, PaP W, crate E, perks S) and rides in
  GENERATED `_tod_breather_data.gsc` from the generator's `BR_FURN` table,
  which ASSERTS every trigger pair ≥ r_a+r_b+64 (the old PaP↔crate 38u rim
  gap mis-sold 5000-point buys; v16.7 nudged the PaP 24u and the station 20u
  onto their panels' axes — read the table, not this line, for coordinates).
  THREE risers per lounge (v13.2: the third
  sits mid-gantry ON the teleporter spur at even (-704,-1120), y derived from
  the arrival point so the ~165u materialize-clearance rule holds by
  construction; v10.12 added the first two after the v6.9 zero-riser
  experiment); the S riser guards the spur mouth from the room side.
  **Tron Grid look — DISTRICTS since v16.11 (2026-09-01, docs/64, artifact
  "Cybercity Tower Facelift")**: the spiral is FIVE colour districts of ten
  floors, `DISTRICTS` in the generator — blue 1-10, green 11-20, orange 21-30,
  gold 31-40, RED 41-50 — each lounge caps its district in its own colour, the
  core band per lap takes the district hue (five stacked bands from the base),
  treads alternate `_tinted`/`_tinted_edge` per floor for rhythm (parapets stay
  plain hue: a `_tinted` parapet is a DECK to the lint). The old 8-hue
  `PALETTE` cycle survives only behind `FACELIFT = false`. Same switch gates
  the DOOR GATES (post + lintel + sill per lap door, slab in the district it
  opens into; `_tod_doors.gsc` slides the slab into the core on purchase,
  `TOD_DOOR_SLIDE`), the BASE PLAZA (floor traces spawn → first door / power
  hall, core foot ring, cyan pilasters + cornice on the arena walls) and the
  TELEPORT BAY colour code (each up pad = its destination lounge's colour,
  LOCKSTEP with `up_orgs` order in `_tod_teleport.gsc`). Pre-facelift look:
  edge-lit `_tinted_edge` floors cycling 5 colors, navy
  base + glowing inlay ring, PaP-material roof floor. **THE SKY IS OURS
  (v17.71, 2026-09-05, docs/104)**: a self-authored synthwave neon-grid
  metropolis rendered by `tools/gen_tod_sky.js` (seamless by construction)
  and wired by the four blocks in `source_data/tod_skybox.gdt`
  (`skybox_tod_cybercity` + `tod_ssi_cybercity`, an ssi clone of Nastian's
  miami_night with ONLY skyboxmodel changed). Miami night (Nastian pack) was
  the sky v1–v17.70 and again v17.78–v17.80 for the yellow-cast A/B (the
  cast was the SUN VOLUME height, docs/107 — never the sky); the cybercity
  pair returned in v17.81 with the fsi, spawn light and light tint left at
  their published values. A sky change is a FULL build; the exposure knob is
  `SKY_GAIN`. **The tower has NO fog** (`apply_fog` calls `fog_off()` on the
  tower; only the spire fogs), so the sky is ~a third of every screen. Music (`_tod_atmosphere` owns the channel):
  **BANDS BY FLOOR** (v9.46) — the track changes as the party climbs past the
  breathers: 1-9 "Password Infinity" (Evgeny Bardyuzha), 10-22 "Cyberpunk
  Futuristic City" (lnplusmusic), 23-36 "Cyber Relay" (Psychronic), 37-50
  "Cyber Eclipse" (bykenneth) — the three climb tracks are spread EVENLY over
  floors 10-50, so only the floor-10 change lines up with a breather. The PANZER's
  track ("Data Spike" — Psychronic) always overrides, and resumes into whatever
  band the party has climbed into; the FINALE track ("You See Big Girl" —
  Hiroyuki Sawano / Gemie) outranks everything and IS the run's clock. One
  `add_music_band()` row per band in `register_music_bands()` — the bands are 10/23/37
  (was 20/30/40, then 10/30/40, evened out 2026-08-25). Rows must stay in
  ASCENDING floor order — band_alias() walks the array backwards. Credit all SIX
  before publish (full list: CREDITS.md). TELEPORTERS (v9.37/v10.3-4): four
  breather pads (0.8s charge, 30s cd) down to a base arrival pad + four base
  UP pads gated on each breather's own lap door — five porters at spawn; band table, wav rules
  and the loudness-matching recipe in sound_assets/tod/music/README.md.
  Bosses: Panzer every 5th round (music + luck-to-last-hit), Rogue Protector
  WAVE every 3rd round, wave size = int(players×round/3+0.5) CAPPED at the
  concurrency roof 8, debt SET not summed (v10.4). REWARDS (v14.5): every
  ELITE (Protector/Reaver/Hound/Sprinter) pays a flat 500 to the KILLER ONLY,
  ×double-points ×BOUNTY (`grant_elite_reward`, one shared TOD_ELITE_PTS);
  the PANZER alone keeps the 1000 team-wide boss jackpot. **Power switch at the BOTTOM.** The generator prints the live
  world-brush / entity / lap counts on every run — read them there rather than
  trusting a number copied into this brief. LED bake is the ceiling; generator
  `PARA_EVERY` is the bake-budget knob.
- HISTORY - the Mage below was retired whole on 2026-10-04; four classes ship.
- **5 CLASSES × 3 TIERS** (`_tod_classes.gsc` `register_gun`; docs/25 —
  CLASS TIERS, 2026-08-22): **the MAGE is the fifth and it is LIVE** —
  `TOD_MAGE_ENABLED` in `_tod_mage.gsh` is **1**, and `TOD_CLS_COUNT` is
  DERIVED from it (`4 + TOD_MAGE_ENABLED`), so the draft card count cannot
  drift from the flag. Exactly one other literal exists, `MAGE_ENABLED` in
  `tod_class_select.lua`, because Lua cannot read a GSC define, and
  `build_map.ps1` Dies if the two disagree. The mage is the map's ONE
  **ADDITIVE** class (docs/114, v18.30): a promotion ADDS the next staff and
  KEEPS the ones below it (`level.tod_classes["mage"].additive`), so "tier 3"
  is a mage holding **lightning + fire + ice at once**, not an ice mage — and
  because they are held together the generator marks tiers 2/3 `flat: true`
  (NO TIER_DPS normalization) and `_tod_mage_elements` applies the same
  step to EVERY staff in script instead. ⚠️ **THAT STEP IS NO LONGER THE GUN
  LADDER AND MUST NOT BE "FIXED" BACK TO IT (v18.51).** It mirrored TIER_DPS
  (1 / 1.5625 / 2.4414) until 2026-09-08, when the user asked for a CURVE —
  *"medium ranked at early mid game, late game High ranked and Very late game
  OP"* — and ranked against the other four classes the old ladder had it exactly
  inverted (rank 2 at tier 1, rank 4 at tier 3). It is **0.92 / 2.00 / 3.95**
  now, so the mage's two promotions are the biggest power steps in the map and
  its floor-30 tier card is the most valuable card any class can draw. VERY LATE
  is not on the ladder at all — there is no tier 4 — it is carried by three
  mage-only multipliers that grow with depth: ARCHMAGE uptime (kill-fed via
  `TOD_MAGE_ARCH_MANA_KILL_LV`), the per-staff card ladders, and CHAIN
  LIGHTNING's arc density. Read the defines, never this line. The mage's
  secondary lookup returns an empty name/stem and `give_secondary`
  removes carried sidearms before granting nothing (v18.48; the old MR6
  placeholder was actually being given, then PaP'd into Death and Taxes).
  No sidearm or grenades: the loadout is three staffs, the LETHAL button casts
  HEALING AURA and the TACTICAL button is BLINK.
  **Ability rules (v18.49):** HEALING AURA needs its first card;
  level 0 has no charges and cannot cast. BLINK obeys its cooldown even with
  god/money/dev flags. Its HUD dims immediately on casting, and stock grenade
  counts/icons cannot overwrite mage tiles. The Rogue Protector's fallback
  damage callback delegates to `upgrade_damage_cb`, so it shares Insta-Kill's
  elite boost and staff multipliers instead of maintaining a partial copy.
  Staff damage uses `staff_mult` / `victim_family` in `_tod_mage_elements`:
  lightning owns the horde, fire owns Protector/armored sprinter, ice owns
  hellhound/Fury, and — since v18.52 — **lightning also owns the PANZER, which
  it was the map's worst answer to until that build** (user: *"Best weapon
  against panzers should be the lightning staff"*). ⚠️ Every prose line in this
  repo said "deliberately the worst Panzer answer in the map" and they are all
  now the OPPOSITE of true; the tax was an implementation reading that left the
  Panzer with no right answer at all. **v18.53 THEN MADE THAT ONE RULE FOR
  THE WHOLE CLASS** (user: *"what makes him OP is that his best staff is always
  top 3 against the weakness enemy"* + *"you can place him right under death
  machine DPS"* — the same instruction twice). **THE CONTRACT IS TWO STATES** (v18.54, user:
  *"his maxed out fire blast should be 1 against their weakness. Easily"* — the
  first pass folded the maxed card INTO the rank-3 target, so six cards bought
  nothing but parity). **UNINVESTED, the right staff lands RANK 3 among the five
  classes' PRIMARY weapons, just under the Death Machine; with that staff's own
  card MAXED it lands RANK 1, and not narrowly.** So the mage is never worse than
  third to anything and is first at whatever it has paid to specialise in —
  breadth by default, peak by investment. Every other class has an enemy it is
  helpless against; this one has none, and has one it is best at. **Lightning has
  no damage card**, so its growth lever is ARCHMAGE (×3.2) rather than a staff
  card, which is why the Panzer figure pinned "right under death machine" is the
  UNINVESTED one. ONE CONSTANT PER FAMILY, and they DIFFER because the staffs do
  (a shared 2.00 left fire and ice at rank 4 and lightning at rank 5):
  `TOD_MAGE_VS_HORDE` 1.30 / `_FIRE_VS_ARMOUR` 3.61 / `_ICE_VS_BEAST` 4.96 /
  `_LIGHTNING_VS_PANZER` 5.60, against `_OFF_FAMILY` 0.45 and `_OFF_PANZER`
  0.40. **Retune by RANK, never by copying one onto another.** They look large
  beside a gun's because every gun figure they are calibrated against carries the
  engine's ×3 head crit and a splash hit takes none — about a third of each is
  buying back a crit the weapon cannot land. **The Warden King is a Panzer**, so the spire's climax is a mage fight
  now. Read the constants
  there for the current matchup rates. Speed **1.00** — read `class_speed_base()`, and
  note a block comment in `_tod_upgrades.gsc` said 0.85 for a day after the
  user raised it. The other four:
  SKIRMISHER **MAC-10 → MP5 → MP7** (speed 1.1),
  ASSAULT **Enfield → Krig 6 → AK-47** (0.9), HEAVY **Stoner 63 → HK21 →
  Death Machine** (0.75), SLASHER **Combat Knife → Wakizashi → STORMBREAKER
  (Leviathan port)** (1.0 — the SKIRMISHER is the map's fastest class, swapped
  with the slasher v14.29 2026-08-30 on the user's "melee is too fast"; read
  `class_speed_base()`, never this line, before quoting a number).
  Once the class gun is PaP'd **AND the player's own climb high-water clears
  the FLOOR GATE** (v14.35 2026-08-30: floor 10 for the promotion into T2,
  floor 30 for T3 since 2026-09-02 (was 20; docs/72) — `tier_floor_ok`, fed by `_tod_gauge::floor_reached`, a
  per-player alive-only maximum that only ever RISES, so you may take the
  promotion anywhere once you have earned it; NOT waived by `tod_dev`, and the
  spire grant stamps `mark_top_reached` rather than being exempted; the player
  is TOLD — v14.39: the card is DEALT AND SHOWN **LOCKED** in its normal right
  slot (so a blocked deal that rolls the tier card is effectively ONE card —
  the user's explicit call over a free third preview slot); the roll asks
  `tier_card_ready_but_for_floor`, only the RIGHT slot is ever lockable (focus
  starts left, so a dead panel is impossible by construction) and a LONE locked
  card is never dealt; the refusal is enforced at `wait_for_choice`'s single
  `want`->`sel` commit and is AUDIBLE. The `TIER 2 AT FLOOR 10` BADGE sits under
  that locked card, or in the panel's top-left gutter (the exact mirror of the
  luck badge slot) when no card is dealt — never both — whenever the floor is
  the SOLE blocker
  (`tier_floor_pending` → the zero-bit `tod_upg_tier_need` eventstring; art
  `i_tod_tier_gate_2|3` behind `USE_TIER_GATE_ART`, docs/50, LUI text is the
  fallback), and the pause CLASS TIER row now shows from tier 1 with the
  requirement in `DETAIL[24].act` — LOCKSTEP: the floor numbers are copied into
  that Lua (the row text AND the `TIER_FLOOR_TO_TIER` floor->tier table that
  picks the badge strip — floor/10+1 broke the day T3 moved to 30, docs/72)
  AND baked into the badge art. Since 2026-09-02 two FREE in-world toasts
  (`tier_gate_toasts`, IPrintLnBold, once per tier) also say it: on PaP below
  the floor, and on clearing the floor. **The PaP prompt is a DEAD lane for
  this and any other custom copy** — `ZMCursorHintNew.lua`'s `isPAPHint` routes
  any hint containing "pack"+"punch" to a static card that never reads the
  string, unless a `TOD_NOUNS` entry claims it first; see CURSOR-HINT ROUTING
  above), 20%
  (v9.42; was 10%) of card deals
  (dev 100%) carry a TIER card (right slot, never auto-locked; **v16.56: a FULL
  luck bar (100) + FULL eligibility incl. the floor gate = dealt 100%**,
  `tier_card_roll` is the one owner on both deal paths): new gun at
  its level-0 form, every GUN-scoped domain reset, class-scoped domains kept
  (the v14.12 list in the upgrade bullet below — never enumerate it here,
  it has drifted twice; TIER_SAFE in the Lua is the mirror). Guns are GENERATED by `tools/gen_tod_twins.js` (ladder table, TIER_DPS
  normalization, never-shrink clips, altWeapon blanked on every form —
  audit it per build) under a 223-registration guard (`LEDGER_GUARD`, raised 200→220→223; 223 is the figure the map ships at with ZERO headroom — map 1's ~230 ceiling).
  Every gun: LOC_NORM 3.0, move 1.0, recoil ×1.15, ADS ×1.20, PaP = +25%.
  **HEADSHOTS ARE 3× FOR EVERY CLASS** — LOC_NORM is the whole story and script
  supplies no per-class ratio. An ASSAULT-only 4× shipped for exactly one build
  (v10.14) and the user reverted it after playing it (v10.16); the recipe for
  bringing it back is in the comment where `class_hs_scale()` used to live in
  `_tod_upgrades.gsc`. Differentiation comes ONLY from the HEADSHOT domain.
  Per-class weapon knobs live in the generator: `CLASS_DAMAGE_MULT` and
  `CLASS_RESERVE_MULT` apply to the **T1 gun only** — the higher tiers are
  normalized FROM the tuned T1, so a class knob propagates by construction and
  scaling them too double-applies it. **READ THE LIVE VALUES OUT OF
  `tools/gen_tod_twins.js`, never from this line** (2026-08-30: as of v14.33 it
  is skirmisher 1.071225, heavy 0.81, assault 1.10 — the skirmisher took two
  −10% cuts that day and will move again).
  This brief said "skirmisher 1.15, heavy 0.90" for an unknown span while the
  constant held 1.3225 / 0.81. Note 1.15² = 1.3225 and 0.90² = 0.81 EXACTLY:
  it recorded the figure for ONE application and never followed the doubling
  when each knob was applied a second time. **A brief that names a constant and
  quotes a number is a second source of truth that nothing regenerates** — name
  the constant, point at the file, and quote a value only with a date on it.
  `node tools/verify_armory_constants.js` catches this class of drift for the
  armory page; nothing yet checks this file.
  **SECONDARIES ARE COUPLED TO THIS KNOB BY DEFAULT** — every skirmisher sidearm
  is capped at `PRIMARY_T1[cls].dps × SEC_CAP_REL[tier]` and sits exactly on that
  ceiling, so moving the class knob moves the shotguns too. That was intended for
  the 2026-08-25 "primaries and secondaries" buff and wrong for the v14.32/33
  primaries-only cuts, which is why `CLASS_SEC_CAP_MULT` now pins the ceiling to
  an ABSOLUTE value. Pin, never derive from something that moves.
  Only the PISTOL (MR6) keeps a script damage multiplier (×9.6 base,
  ×5.76 PaP — the PaP form took a 40% nerf 2026-08-23).
  Move speed is keyed on the CLASS (`class_speed_base()`), not the gun, so it
  survives any roster swap. Sound aliases for all class guns are GENERATED by
  `tools/gen_tod_sounds.js` — it reads each GDT for the alias names it
  actually references (guessing from wav names is wrong in both directions)
  and skips fire families a gun lacks (the Stoner has no trig_pull). Game-start CLASS DRAFT (`_tod_class_select.gsc`
  LUI, 30s, random on timeout) + hold-USE stations at the base (moved WEST of
  the door trigger — overlap bug); switching swaps the primary, per-player
  upgrade levels persist.
- **THE TWIST — endless rounds:** there is NO pause between rounds. The moment
  the last zombie of a round SPAWNS, the next round starts — it should feel like
  the round never ended. Implemented in
  `scripts/zm/zm_tower_of_doom/_tod_endless_rounds.gsc` via the stock overridable
  pointers `level.round_wait_func` (wait for zombie_total==0, i.e. all SPAWNED,
  not all dead) + `level.zombie_round_change_custom` (no fanfare stall) +
  `level.func_get_delay_between_rounds` (returns 0).
- **Zombie speed curve** (`_tod_zombie_speed.gsc`): SPRINT animation from
  round 1 at reduced rate (floor 0.8 after live test — 0.5 read as broken),
  linear to full sprint at `TOD_ZSPEED_FULL_ROUND` (**18** as of 2026-08-29;
  7 -> 10 -> 12 -> 15 -> 18 across four user retunes, and that number is the
  end of this lever — see the block comment on the define; THIS BRIEF SAID 15
  for a week after the code said 18, so read the define), then
  `TOD_ZSPEED_STEP`/round after it, LINEAR and uncapped (**0.21%** as of
  v18.2 2026-09-06, user "lower that by twenty five percent"; 0.35 -> 0.28
  2026-08-26 -> 0.21). 1.5s keep-alive sweep re-asserts
  gait+rate (one-shot overrides decay — map 1 lesson). Spawn trickle 0.8×
  stock, floor 0.3s.
- **Perk power-on glow** (`_tod_perk_lights.gsc|.csc`, ported from map 1):
  server sets the `todPerkGlow` clientfield when "power_on" flags; client
  PlayFXOnTag's the colored aura (server-side PlayFX does NOT render). FX =
  map 1's self-authored recolors, sources in repo `share/raw/fx/acc/light/`.
- **Perk loose change** (`_tod_perk_scatter::loose_change_watch`): stock BO3
  prone-in-bump-area reward, 100 points + purchase sound, first player per
  machine per match; no purchase or power required. The existing bump follows
  each move. `level.tod_scatter_change_claimed` is keyed by the same stable perk
  key as the machine roster (one machine per perk), never by pad or player;
  shuffles, deaths and joins do not reset it. Do not also enable stock
  `zm_perks::spare_change()` or rewards would have two independent owners.
- **UPGRADE TOWER** (`_tod_upgrades.gsc`): events at rounds 1 (post-draft),
  4, 8, 12… (dev: every round) — the world pauses, each player picks 1 of 2
  rolled options (**43** live domains as of 2026-09-08 + the TIER card × rarity
  REGULAR/SUPER/ULTIMATE = +1/+2/+3
  Lv; ids run to **55** — `domain_id()` and the Lua tables are
  KEY-KEYED, so a removed domain's id STAYS mapped and only its `add_domain`
  call goes. **NEVER QUOTE THE COUNT OR THE RETIRED-ID LIST FROM THIS LINE** —
  both have been stale here more than once, most recently naming PERK SLOTS as
  retired for five days after v17.3a restored it. `node
  tools/verify_armory_domains.js` prints the live count, the persist count and
  the highest id in one second and is the only figure worth repeating). v14.11 rebalance (2026-08-30): heavy = the TANK (new VITALITY
  id 38 +10HP/Lv ×5 scope-class, new RECOVERY id 39 regen-starts-sooner ×3;
  REGEN and assault BACK ARMOR gone, MOBILITY capped 5); slasher trimmed
  (CLEAVE max 3, no SPRINT ARMOR, DR capped 5 via the bonus_max-as-override
  lane); RUN AND GUN pays free shots AND bonus damage while moving on ONE
  stage table (v16.50: 5 levels, 16/28/38/46/52% — LOCKSTEP duplicate
  constants across _tod_upgrades/_tod_runandgun plus DETAIL[23] — change all
  three; read `TOD_RNG_PCT_L*`, never this line); MOMENTUM
  removed, SECOND WIND is the MP5's unique (MP7 keeps only ADRENALINE).
  v14.12/13: HEADSHOT + SCAVENGER persist through promotions — SCAVENGER
  for the ASSAULT ONLY (set_scope's scope_class lane, v14.13;
  domain_survives_tier is the one authority). The pause reset badge is
  SERVER-COMPUTED: sync_max() packs a survives bit into every tod_upg_sync
  max arg (+100, int-packed — no 4-arg LuiNotifyEvent exists in-tree);
  TIER_SAFE in the Lua is only the nil-fallback now. Persistent set:
  DR/LUCK/SPRINT/SPRINTFIRE/SPRINTARMOR/BACKARMOR/VITALITY/HEADSHOT/
  SCAVENGER(assault).
  **CARD ART CARRIES THE NUMBERS BAKED IN, so a domain retune is not finished
  until the card is re-baked** — the card is the only place a player ever reads
  the value. Audit + prompts: `docs/33_upgrade_art_audit.md`. When auditing,
  OPEN THE PNG; the art-prompt docs go stale (docs/26 still specifies a KILL
  RELOAD card that was re-baked out from under it).
  Odds ride the **LUCK BAR** (`_tod_luck.gsc`, 0–100% per player: kills
  normalized 40×players÷round_total, headshots ×1.5, revive +15, door +8,
  down −25, boss LAST HIT takes all; FULL RESET to 0 after each event; LUCK
  domain = +10% gain rate/Lv). **OVERCHARGE (v14.9)**: the bar SECRETLY tracks
  to 150 (HUD + pips capped at 100 — the band is invisible); at exactly 150
  the bar art zap-animates (todUpgLuck spare values 11..14, server-cycled) +
  a per-client semi-deep zap fires every 3s up to seven times per overcharge
  (`TOD_LUCK_OVER_ZAP_LIMIT`; animation continues silently), and the deal guarantees BOTH
  non-tier cards ULTIMATE (LOCKSTEP TRIO: TOD_LUCK_OVERMAX /
  TOD_UPG_GUAR_BOTH_BAR / TOD_UPG_LUCK_OVERMAX_PCT; contracts + art/SFX
  prompts in docs/45). **NO-TWIN RULE: upgrades are NEVER weapon
  variants** (engine ~230-twin boot-AV ceiling, map 1 docs/21 §A) —
  damage/firerate(echo-proc)/magsize(virtual pool) are all script-side.
  UI = real LUI (`tod_upgrade.lua` + `_tod_upgrade_ui.gsc|.csc`, 18
  clientuimodel fields = **61 bits, the PROVEN ceiling — APPEND ONLY**);
  luck bar = LuckSegs segments in the frame art (todUpgLuck, live via
  `tod_upgrade_ui::set_luck_pct`); owned-upgrades list shows ONLY in the
  pause menu (int-only `LuiNotifyEvent(&"tod_upg_sync")` → `CoD.TodOwned` →
  AetheriumStartMenu.lua panel — `SetClientDvar` does NOT exist in T7).
  **PERSONAL UPGRADE STATION** (base, core south face, Chaos PaP mesh):
  solo upgrade buy at a FLAT 3000 (the 2000 +250/purchase ladder was RETIRED
  with the triggerstring-250 crash fix — the price must stay a single
  constant, or at least never reach the hint literal; see station_cost()
  and the triggerstring-250-cap memory), 5 uses per station and 3 at the
  CROWN ALTAR (id 5 — v17.37 2026-09-04; it was UNLIMITED 08-29..09-04, a
  call made while the price LADDER still bound it, and the ladder went flat
  with the crash fix. Read `station_use_cap()`, not this line); **the world pause is PARTY-SIZE CONDITIONAL since v16.84
  (2026-09-03)** — CO-OP does NOT pause (the risk, as it always was), SOLO
  freezes the world AND the buyer exactly like a round event, through the same
  `set_world_pause`/`menu_freeze` pair, because the risk model was always a
  co-op argument and one player has no teammate to absorb it. `station_freeze_wanted`
  is the ONE gate (party size, then the FINALE carve-out: the closing song is a
  clock a freeze cannot stop, so the crown altar stays live-world once
  extraction is called). Three behaviours ride `level.tod_upgrade_pause` and
  therefore flipped for free in solo — the reveal plays at FULL speed, the
  damage callback returns 0, and EVERY card-panel input lane opens (v16.81's
  d-pad-only station rule was earned by the player being mid-fight). The raw
  `tod_upgrade_pause` read STOPPED being a takeover test the moment the pause
  became self-inflicted: `level.tod_station_pause_owner` + `station_owns_pause()`
  is the difference, and `run_upgrade_event` CLAIMS the pause at its takeover
  notify so its own unpause can never clear a station's freeze. 15s timer; a
  scheduled round OVERRIDES a manual pick and the
  same cards re-present after (re-clamped — stale cards never lower levels).
- **HUD: Aetherium kit** (vendored, `zone_source/aetherium_hud.zpkg`) + our
  LUI menus. No Mega Bottles, no Data Shards — old map's systems, NOT ported.
- **THE CROWN + THE ENDING (v9, user 2026-08-21).** Above the spiral:
  CROWN STAIR (gold) → TERRACE → CAUSEWAY ("the pathway") → CROWN HALL, a
  1536-sq open-top citadel floating beside the tower, + a MAST on the core top.
  **v11 (2026-08-25) — THE CITADEL IS A LITERAL CROWN.** The user's verdict on
  the old one was "it just looks like a castle with spikes"; measured, it was a
  4°-wide blue box plus six spires under the 0.5°/384-unit legibility floor,
  standing on a `dark_blue_tinted` underside that rendered as a black square
  against the fog. It is now THE CIRCLET (`gen_tower_map.js` §5f): a
  **6128 wide x 13,888 tall gold crown** (v11.1, user: "I want the scale to be
  even more... players should be in awe") — ONE KNOB, `CR_SCALE` (1.4), scales
  the whole thing uniformly; the SOUTH FACE is PINNED at y=6912 because the
  mouth has to stay inside the causeway F approach, so the crown grows NORTH
  around the hall and `CR_CY` is derived. Flared 9° band, white
  ermine rim, 16 alternating points (8 crosses pattée / 8 fleurs-de-lis, every
  head WIDER than its shaft), a FRONT CROSS with a great ruby, two dipped
  arches → monde → cross finial → red beacon, 16 jewels, pendilia, and —
  v12 (user 2026-08-26: "they look up and see this MASSIVE building") — THE
  VORTEX BELL underside: 10 tiers on an ogee whose ring-widths accelerate
  toward the centre, corona teeth serrating the gold tiers, jewel collars on
  two brass tiers, ermine tail-spots under the south rim, pearl beading on the
  arches, and THE GIRANDOLE — a stepped ruby drop-pendant (with the crown's
  third red light) hanging below the bell, completing the red vertical axis
  (beacon above, great ruby front, girandole below). The causeway runs
  **through a 640×424 mouth cut in the rim**. THE HALL DOES NOT MOVE — floor,
  walls, gate, dais, sconces, exfil pad and every `_tod_crown_data.gsc` anchor
  are byte-identical; only `pylon_orgs()` moved. Full record + the 15-point
  "castle vs crown" checklist: `docs/34_crown_redesign.md`. Iterate with
  `tools/preview_crown.js` (6 renders, ~1s, no bake) — **if the `_under` view is
  dark, nothing else you did counts.** The 4 hall pillars are BACK as pure
  architecture (v12 — the v11 deletion was aimed at the coil MODELS; user:
  "I think the last agent thought I wanted the entire pillars removed"): gold
  base, ruby shaft, gold cap at the original ±448 spots, scenery + cover only.
  The finale's quarter-progress read STAYS on the crown's corner points
  (`pylon_orgs()` untouched). The hall also has its own AMMO CRATE (v12, east
  wall, mirror of the upgrade station) — coords ride in generated
  `_tod_crown_data.gsc::crown_crate_org()`, clip emitted by the generator.
  **Generated as lap LAPS+1 in the spiral's own parity math** — every
  crown coordinate is authored in the odd frame and mirrored by `CM`
  (`cbox/cpt/cyaw/cvolume/cspec`); the old odd-only "final landing" special
  case silently vanished when LAPS went even and left the roof unreachable.
  Never special-case the top by parity again. **THE LAST MILE (v10)** — the
  CAUSEWAY IS the finale arena; `SKY_IN` and `HS` are derived from `CW_LEN`,
  never literals. **v12 (user 2026-08-26: "the paths ... are pretty simple and
  straight forward. Lets be more creative ... scary and anxious") — 7360 long,
  160 wide, SAME span budget as v10.12 (so every crown/road assert held), but
  every lane is now a DIFFERENT KIND of fear**: gate-run (flanked by the first
  AVENUE PYLONS — jewelled gold obelisks floating in the void, the road's
  scale-rhythm markers) → fork (west THE RIDGE climbs +256 and ZIGZAGS along
  the crest — the awe lane, best crown view on the road; east THE BROKEN STAIR
  steps down through blind pockets into a 640-long hollow at −256, then one
  16-tread blind climb) → merge → **THE NARROWS** (the old spine, PINCHED to
  120 wide for its middle 320 under portal 2 — the road's one guaranteed
  single-file choke) → **three-way** fork (west THE UNDERCROFT plunges −384
  to an ambush cistern then 960 units of blind ascent; centre THE PLANK, 120
  wide, raised to +256, the riser-densest straight line; east THE WEAVE, flat
  but serpentining through 4 jogs — 9 pieces, 9 risers, the most infested
  ground) → merge → approach → a FLARE into the citadel gate. Boss
  altitude-sorting (panzer→highest player, protectors→lowest) makes the plank
  draw the Panzer and the undercroft draw the swarm — emergent, by design.
  Shortest walk ~8220 units (the generator prints the live number) against the
  90 s road phase — comfortable even for HEAVY (speed 0.75), so the risk at
  the ending is being PINNED, not being slow.
  The citadel mouth FLARES to `CW_FLARE` because the gate opening is 256 and
  the road is 160: the difference was unguarded hall floor over a 19,000-unit
  drop. The mouth PORTAL must be as wide as the flare or the rail pass plants
  bollards on the citadel floor — `roadEmit` throws on that now.
  **THE ROAD IS DECLARED, NOT DRAWN.** `roadFlat`/`roadStair`/`roadPortal`
  declare flat grid-aligned deck cells; `roadEmit()` rasterises them on a
  20-unit grid and DERIVES every rail. `ROAD_G === PARA === 20` is load-bearing:
  it makes a rail occupy exactly the one unoccupied column outside the edge it
  guards, so a rail can never land on deck. roadEmit also throws on overlapping
  cells, on any adjacency over `ROAD_STEP_MAX` (18), and if the citadel mouth is
  not reachable from the terrace mouth. Hand-cut rails (the v10.11 `face()`
  walking mouth x-centres) do NOT survive a road that turns — that is what this
  replaced.
  First and last runs are **on-axis at TOP2** — load-bearing, they meet the
  terrace mouth and the hall's gate opening. Every branch returns to TOP2 before
  a merge, so junctions are always flat. A `tod_causeway_gate` script_brushmodel
  **seals the mouth until EXTRACTION is bought** (same
  `Solid+DisconnectPaths` → `Hide+NotSolid+ConnectPaths` contract as every
  door); while it is shut `_tod_endless_rounds::finale_spawn_selection` drops
  every riser past it, or zombies strand on an unreachable bridge holding actor
  slots. Risers/lights/portals come from `causewayRunPoints()` etc. — placed
  **by shape, never by fraction of length**, since most of the road is no longer
  at x=0 or at TOP2. A CROWN RESPAWN GROUP sits on the terrace (gated on
  `roof_zone`, like the breather groups are gated on their lap zones) — without
  it a co-op death during the 191 s finale sent that player to the base arena,
  which is removal from the run, not a setback. It is on the TERRACE and not in
  the citadel deliberately: you come back at the START of the road.
  **THE BAKE IS A PASS/FAIL GATE, NOT A BUDGET METER** (corrected 2026-08-25):
  on near-identical input this map has baked at 38.2, 126.2, 35.1, 31.9, 31.3 and
  31.8 s. The 126.2 was taken ONCE, was used to justify a design limit, and NEVER
  REPRODUCED — an A/B with byte-identical geometry (only materials differing)
  ruled that suspect out too. Bake time here is dominated by HOST STATE, not map
  content. Never conclude anything from a single bake; run
  `node tools/measure_lit_area.js` for the budget question (deterministic,
  instant, groups area by map region) and read _bake_test only as BAKED/CRASHED,
  and the same map varies by 20 s run to run. Bake and read the number; never
  predict it, and never use it to justify not adding geometry.
  Finale = `_tod_finale.gsc`: buyable EXTRACTION
  **12k** (v10.11, was 25k — the price stopped being the gate once the gate
  became a literal wall) at the **terrace** (start of the road) → the closing
  song takes the channel and IS the clock → ~8220 walked units of
  ambushed road (v12; the generator prints the live number) → survive to the last chord → "YOU ESCAPED THE TOWER" via
  `custom_game_over_hud_elem`. `TOD_FINALE_SONG_SECS` + `DEPART_SECS` must
  equal the wav's length (191 + 6 = 197.4) or the LOOPING stream restarts under
  the ending. Ambush = spawn-delay floor + `_tod_bosses::finale_pressure_start`
  cycling all three boss types under a combined roof of 4 — **no stock AI limit
  is ever raised** (bosses are direct SpawnActor and bypass stock's gate).
  Anchors ride in from GENERATED `_tod_crown_data.gsc`. **Boss-fight slot:**
  `level.tod_finale_boss_fn` owns the hold-out if defined. Rails everywhere
  carry invisible clip caps (`RAIL_CAP_H`) — rail tops are not launch pads.

- **THE ENDLESS SPIRE (v14.0, 2026-08-29, docs/44)** — the post-victory
  endless mode, THE MAP'S HARD MODE by design (the v13.24 base tone-down was
  justified by its existence). The finale win no longer auto-departs: THE
  CHOICE — the exfil pad EXTRACTS (old ending) or the dais teleporter ASCENDS
  the party (first committed hold wins, ONE WAY) to a second **70-lap** tower
  at x=+10240 (generator SECTION 6, `SPIRE_ENABLED`; **`SP_LAPS` 70 since
  v17.69, 2026-09-05, docs/105 — it was 100 from v14.0; the user's "go to
  floor 70 instead of 100"**; monochrome red, gold hubs every 10th floor (7
  of them), crate shelves floors 5+, THE TOP one flight above hub 70's hall:
  **THE SUMMIT ARENA + THE WARDEN KING (v17.70, 2026-09-05, docs/106)** — a
  1408-square deck over the last hall (it ROOFS THE THRONE; generator
  `SP_SM_*`), the stair's mouth sealed by `tod_spire_summit_gate` on the
  hall-gate contract, a 1000-point crate, and ONE Panzer at 10M HP PER PLAYER (25M until the co-op curve pass; corrected here 2026-09-10) capped at four (up
  to 100M; NOT the "flat 100M" this line claimed until 2026-09-07)
  (`TOD_KING_*` in `_tod_spire.gsc`, `king_run`): everyone on the deck →
  seal → 10 s → he lands → a FROZEN max-out (`tod_upgrades::king_max_out`,
  then `king_dark_deals`: dark-only 10 s deals until nobody has one, everyone
  held frozen by `level.tod_king_hold`) → the fight (a second flame
  cone + summons every 18 s). ⚠️ **HIS FLAME IS DOUBLED IN BOTH APPEARANCE AND HURT BOX** (corrected
  2026-09-10 — the 2026-09-07 "check" that wrote the opposite here MISSED
  `king_setup`'s own `trigger_box( 400, 100, 50 )` swap, v17.70, which the
  pack's burn loop reads every tick as `self.flameTrigger`): the FX half is
  `_tod_spire::king_flame_fx`, an FX host linked `TOD_KING_FLAME_FWD` 140u
  ahead of the muzzle; the damage half is that trigger swap. There are no
  "re-registered BT twins" — `mechz_spiki`'s damage cone
  (`acc_player_flame_damage`) has no `tod_king` reader, and the ONLY readers of
  `self.tod_king` anywhere are the gauge, the upgrade max-out, the Wisp Tea tick
  cap and the Gift of Death divisor. So the visual overhangs the hurt box by
  140u. Known and deliberately deferred since v17.95 (memory
  `changelog-is-not-the-code`); v18.9 chose to fix the record, and v18.14 took
  the matching claim out of the store page → `king_win` unseals the extraction. **THE MAX-OUT FREEZE IS A REAL FREEZE SINCE v17.94** (first real run, 2026-09-05: Furys bamfed onto frozen players through the deals): `boss_pause_watch` re-asserts every elite's freeze PER TICK (the Fury archetype re-stamps its own anim rate on every bamf/teleport end), a Fury is PARKED at its tree's idle gate (`tod_bt_idle_on_pause` → `zombie_think_done = false`, the parked-riser statue mechanism used on purpose), the seal zeroes all four family debts (trial VII's leftovers were the Furys), and `set_world_pause` makes every upright player INVULNERABLE for as long as any world pause holds (`tod_pause_invuln`, released only by the pause and only if zombie blood / depart / summit win do not hold it). **THE SPIRE GAUGE
  IS HIS HEALTH BAR** (`level.tod_king_hp_frac` → `_tod_gauge::finale_cell`,
  full to the summit, draining). He is the ONLY Panzer — but the gate is
  `level.tod_trial_active`, which `king_run` sets at the seal alongside
  `tod_king_active`; the director's Panzer branch reads ONLY the former.
  `level.tod_king_active` is WRITE-ONLY (two writes, zero readers, confirmed
  2026-09-07) and this line named it as the gate until then. Read the defines, never this line;
  beacon z=27584 — visible from the whole climb, deliberately.
  `SP_LAPS` must stay EVEN, so "one more floor after the last trial" is a
  parity-mirror job on the summit block, not a number change). On ascension `_tod_spire.gsc`
  runs: THE GRANT — **v16.36 (user 2026-09-02): YOU KEEP THE BUILD YOU BEAT
  THE TOWER WITH.** The grant is now ONLY EVERY PERK (v16.80 dropped the PERK SLOTS gift)
  the map sells + ammo/health; the T3 promotion, the free-PaP latch and the
  domain max are GONE (v14.0-v16.35 granted all of it), and the luck bar is
  kept because it prices the trial deals. **PERMA PERKS:** stock still strips
  perks on a down; `perma_perks_watch` re-gives the roster after every
  revive and `on_spire_spawned` (the spire's first `callback::on_spawned`)
  after every respawn and for late joiners — NOT `_retain_perks`, which
  leaves `num_perks` zeroed by stock's spawn and the give-threads dead. Solo
  Quick Revive is a LIFE: withheld on the revive lane in solo, handed back on
  ascension and on every WON TRIAL. **A WON TRIAL IS THE SPIRE'S ONLY
  UPGRADE SOURCE** (`trial_upgrade_deal` → the real `run_upgrade_event`; the
  round clock stays suppressed). No cap arithmetic since v16.80: the perk
  limit is a constant above the roster, so every perk fits with nothing to
  grant (the PERK SLOTS gift went with the domain).
  The spire has NO upgrade altars — `station_spawn` places base 0, breathers
  1-4, crown 5 only; hub vendors are PaP + crate ONLY (`SP_FURN` — the two
  hub perk pads were RETIRED v17.56, 2026-09-04: every perk is perma-granted
  on ascension, so a spire machine was a prop that could take 4000 points for
  a perk already held), and
  PaP must stay because a tier card needs the class gun packed. Mule Kick is
  not granted (RETIRED; a bare HasPerk of it raises the weapon limit to 3), TOWER TEARDOWN (deletes the old world's
  script entities — the ~1024-gentity budget is the spire's binding
  constraint), perk machines are RETIRED at the ascension
  (`_tod_perk_scatter::retire_all`, v17.56 — parked under the spire, triggers
  disabled, watchers stopped; the roster keys survive because
  `perma_perks_give` reads them; v14.0-v17.51 migrated them onto spire pads
  instead), music → `tod_music_spire` (Suno "Neon Static", single
  band row, Panzer override intact), spawn pacing HOT (0.18 floor — lockstep
  pair in _tod_spire.gsc and _tod_endless_rounds.gsc) **and the ROUND BUDGET
  HALVED** (v16.9, user: "each round was like 15 minutes" —
  `tod_max_zombies` on stock's `max_zombie_func` hook, `TOD_SPIRE_BUDGET_DIV`,
  **1.25 as of 2026-09-04** — 3 shipped untested, the user walked it to 2 the
  same session, played it, and found the round COUNTER racing ("rounds progress
  too fast ... half it. Maybe even 60% less faster"), so 60% of the speed-up was
  given back; read the define's own LEDGER block, never this line;
  at depth the round clock is budget ÷ kill rate because spawning stalls on
  the 45 ai_limit, so the trickle floor cannot move it). Doors sequential
  (ONE live buy at a time, flat 6300 since v17.70 — 9000 v17.10, 4500 v16.30,
  3000 before — through
  door_price; the base rides GENERATED `door_cost()`, never a script literal), crates in a
  ±3-floor lazy window. Wipe = "THE CLIMB ENDS HERE"; summit extraction
  @7500 = "YOU CONQUERED THE SPIRE". _tod_finale ↔ _tod_spire talk ONLY by
  level notifies (tod_choice_begin/tod_ascend/tod_extract) — no import
  either way, each no-ops without the other. Anchors ride GENERATED
  `_tod_spire_data.gsc`. The lint carries spire-island proofs (own flood,
  arena→summit, own detachment bucket) — but a GEOMETRY flood and a NAVMESH
  flood are DIFFERENT CLAIMS, and the spire is the case that proves it: it
  shipped lint-green in v14.0 with ZERO navmesh (cod2map only flood-grows mesh
  from seed entities — navmesh.json seeds — and the detached island had none),
  so every zombie on it was inert until v14.19 seeded it (22 node_pathnodes,
  generator §6f; memory `navmesh-is-seeded-flood`). Any NEW detached region
  needs its own seed + a FULL build. **THE NAVMESH IS NOW READ, NOT INFERRED
  (2026-09-04, user: "random spots on the map zombies won't attack you ...
  around floor 42-44 ... spots where you just can't get targeted").**
  `tools/lint_tod_navmesh.js` decodes the `.hkt` cod2map wrote (faces, edges,
  vertices — format in its header) and runs as a HARD GATE after cod2map on
  every full build: each tower must be ONE connected component. The shipped
  mesh was **18 islands**, every seam inside the E flight of laps 17/19/33/39/
  43 on BOTH towers (floor 43 = that report; lap 17 = the v17.7 "no mesh above
  floor 17" ceiling, which was this seam plus pruning). Seeds, the .hkt byte
  size and cod2map's transcript all read CLEAN on that mesh — only the faces
  showed it. Cause: the ramp wedge's top passed EXACTLY through every tread's
  nosing edge, so each flight gave Havok a walkable plane with fifteen
  coplanar contact lines; its overlapping-triangle fixup left unstitched
  slivers on laps whose plane arithmetic rounded badly. Fix: `RAMP_LIFT` (2)
  in the generator lifts every wedge above the nosings — 18 → 2 components
  (tower+crown road, spire). Zombies chase `player.last_valid_position` and
  need a PATH to it, so "won't attack HERE" is always a mesh question; ask
  the lint before theorising about seeds. ⚠️ SHIPPED BOOT-VERIFIED BUT THE
  POST-WIN LADDER HAS NO REAL RUN (and could not have run before v14.19) —
  tools/spire_wip/WIRING.md §10 is the ladder, HARNESS.md the fast-path recipe.
  **THE WARDEN TRIALS (v16.15 → v16.19, docs/66) — every spire hub (floors
  10..100) is THE HUB HALL: the tower's centre opens for the fight.** At a
  hub lap the core column STOPS at the hub's mid landing and resumes 576
  higher (generator §6b segments, ending UNDER the hall slab), and a DRUM of
  plain-red walls (632 tall, 20 outside the parapet line; generator
  `SP_RM_*` + `SP_FURN`, asserted like `BR_FURN`) encloses the whole
  872-square cross-section: a hall floor at the hub landing over the core
  footprint + the E/N galleries + the NW region (which roofs the W flight's
  lower half; the flight climbs into the hall through a 160-wide STEPPED
  FAN at its top — v16.21: treads 12..15 each get a run of 12-high slabs
  rising eastward to hall level, every adjacency in the fan one step, one
  wall on its north edge — and the floor's edges over the slot carry
  on-floor rails), the hub's own S flight climbing INSIDE the drum behind a
  stepped inner wall from the corner (the lane under a stair is void; that
  lane is OUTSIDE the seal),
  the next lap's E and N flights running round the inside of the drum as
  railed galleries 192/384 up, four cover pillars (NONE in the doorway's SW
  corner), a floor ring + the TRIAL MARK, vendors on the walls, six risers.
  No crate shelf on the floor after a hub (it would jut through the drum).
  THE SEAL IS THE HALL GATE (v16.21): `tod_spire_hall_gate<hub>`, a
  script_brushmodel across the fan's mouth on the crown door's proven
  Show+Solid+DisconnectPaths contract (hidden at init, shown for the trial,
  hidden again on the win) with Shadows of Evil's ritual-barrier FX along it
  (`zombie/fx_ritual_barrier_defend_door_wide_zod_zmb`, the purple lockdown
  wall, three tag_origin hosts spread on the gate's axis at yaw 0 — the one
  number to flip if it renders edge-on). v16.19 sealed DOOR n one flight
  below instead: the floor locked, the room did not, and the first real run
  (2026-09-02) walked out of the hall onto its own stairs. `trial_box` is
  the HALL ALONE (the W flight's slot and the S lane are out). No honour
  guard at hub doors. SEVEN LAYOUTS since v17.69 (ten from v16.21 to v17.68;
  `SP_RM_LAYOUTS`: pillar/post/low wall/dais/big pillar — and since v17.86
  (docs/109, user 2026-09-05: "each one to have its own personality ... a
  story for each") TALL walls, bar FENCES, LAMP pylons, PLAT steps, a THRONE,
  LINTEL beams and wall PANELS — asserted clear of
  the approach lane, the seven gallery risers, spawns, vendors, the Warden
  drop, UNDER the E gallery flight and, for hub 70, under the summit CAPITAL
  that roofs that hall's centre at 192 — PLUS a `hue` that colours all five
  hall lights AND, since v17.86, picks the hall's whole material KIT
  (`SP_HALL_KIT`: floor, inner walls + a drum LINER band, lamps, panels,
  step, sigil — the drum's outside and the gold band stay gold), and a `sig`
  floor SIGIL inlay, asserted clear of everything. Plan views:
  `node tools/preview_trial_halls.js` (from the EMITTED brushes, ~1 s))
  matched to SEVEN RECIPES (`trial_recipe`: which elite family carries the
  adds — sprinters included — extra Wardens, the frenzy's timing): THE RING
  (gold), THE KENNEL (green), THE FIRING LINE (cyan), THE ALTAR (purple), THE
  MAZE (orange), THE GAUNTLET (white), THE THRONE (red). Names, colours and
  fights are the table in docs/105 §A.2; the banners carry the same colours.
  **FOUR TRAPS THE GEOMETRY LINT'S FLOOD CAUGHT (2026-09-02)**: a rail on
  the NE landing's inner edge sat ON the N flight's first tread — that edge
  IS the flight's mouth — and severed the climb; a wall from the hall's SW
  corner shared the doorway's 20u cell; the SW pillar left a 20-wide slot;
  the post-hub shelves cut through the drum. Bisect recipe: an env-gated
  skip per piece + a patched lint copy that lists detached nodes by brush
  (CHANGELOG v16.19). **THE HALL
  CLOSES ITSELF the moment every living player is inside it**
  (`trial_watch_all` — ONE watcher over every hub from ascension, v16.21;
  the v16.15 per-hub watcher armed on the door BUY, which is one path of
  several into a hall: a 2 s tell at the gate and the mark, then a re-check; a downed teammate outside holds
  it open — user 2026-09-01: "once everyone is in the holdout starts and
  gets locked off from leaving"; the v16.15 hold-USE altar is GONE) and
  runs a `TOD_TRIAL_SECS` (70 since v17.8 — 60 for an hour that evening, 90 before, 120 originally; `TOD_TRIAL_FRENZY_SECS` is DERIVED as a third of it, so the length is one number) hold-out: wipe, seal, WARDENS (Panzers via
  the honour-guard direct-spawn
  lane: one per player, +1 in the last `TOD_TRIAL_FRENZY_SECS`, cap 4,
  replaced `TOD_TRIAL_WARDEN_REDROP` after a fall), adds per the hub's
  recipe (protector/reaver/hound/sprinter debts), every elite spawned inside
  ×`TOD_TRIAL_HP_MULT`
  (boss_hp reads `level.tod_trial_hp_mult`; THE LADDER, re-set TWICE from
  real runs and therefore the LAST thing to quote from memory — read the
  `TOD_TRIAL_*` defines at the top of `_tod_spire.gsc`: v16.21 took the
  v16.15 numbers ×0.85 with a 1.07 step, v17.8 took THOSE ×0.75 with a 1.08
  step (trial I HP ×0.956 / tick 5.75 s, trial X ×1.911), v17.69
  COMPACTED TEN STEPS INTO SEVEN at the SAME TOP: step 1.1225 (= 1.08^9 ^
  1/6), so trial I was unchanged and trial VII was the old trial X — user
  2026-09-05: "compact 1-10 difficulties into 7 ... bigger jumps"; and
  **v18.2 2026-09-06 FLATTENED THE RAMP, step 1.1225 -> 1.09** (user: "many
  people are complaining about how hard the trials get as you continue to go
  up ... lets make it a bit easier as you continue") — trial I still does not
  move, trial VII goes ×1.911 -> ×1.603, and the same pass's -10% on every
  elite lands on top of it; earlier
  users: "toned down about 15% … 7% increments", then "starting off way too
  hard … about 25% easier … 8% harder each level"), trickle at
  `TOD_TRIAL_SPAWN_FLOOR` 0.12 (LOCKSTEP pair with `_tod_endless_rounds`),
  its OWN track (`tod_music_trial`, "Chaos Unleashed" — v17.8; it was the
  boss track until then, and it is level-matched to that track rather than to
  the band tracks, since it replaces it at the same alias volume),
  the tower gauge as the clock (the finale's `tod_finale_song_*` lane —
  `finale_cell` sizes itself with `cells_for_mode()`, so a trial fills all 35
  spire cells and `trial_win` clearing the two fields drops it back to
  altitude), and
  the door ABOVE the hub (11, 21 … 61) plus the summit extraction for hub 70
  SEALED until the clock runs out (`trial_seal_window`, one shared literal).
  The win's purse is 5000 + 1500 per tier past the first (trial VII 14000 —
  the old trial X's purse; 1000/tier until v17.69).
  **NO CEILING IS RAISED**: the Wardens get FIRST CLAIM on
  `TOD_ELITE_ROOF_ALL` through `level.tod_trial_reserve` (read by
  `elites_over_roof`), and `level.tod_trial_box` contains every spawn —
  risers in `finale_spawn_selection`, bosses in `pick_spawn_point` — inside
  the ring, the sealed-crown `in_hall` rule one flight up. Wardens pay the
  elite rate (`tod_spire_guard`); the win pays `TOD_TRIAL_WIN_PTS` 5000
  team-wide + a Max Ammo on the mark + **AN UPGRADE CARD DEAL to every living
  player (v16.36, `trial_upgrade_deal` — the spire's only upgrade source)** +
  the perk top-up (a no-op under perma perks except the solo Quick Revive life).
  **THE REWARD IS A FROZEN WORLD FROM THE LAST CHORD (v17.61, user
  2026-09-04: "make sure to freeze the game during the trials reward")**:
  `trial_win` calls `set_world_pause( true )` BEFORE any reward lands and the
  deal releases it after the last pick (`trial_upgrade_deal` releases it
  itself on the empty-deal path). Before v17.61 only the deal froze, 3 s after
  the win, and those 3 s were a live hall under the WON plate. Players are
  NOT frozen by the win — the cards freeze participants as ever. The summit
  extraction refuses during any freeze (same gate as every spire door). The
  Max Ammo drops with stock's `b_stay_forever` and gets stock's own
  `powerup_timeout` started on it when the freeze lifts (`trial_ammo_drop`) —
  its ~26 s real-time life used to run out under the cards.
  ⚠️ ONE REAL RUN (2026-09-02, dev build, hub 10 only): the fight ran, the
  lock was in the wrong place, the entrance was too small — all three
  reshaped in v16.21 and UNPLAYED since; the harness in
  HARNESS.md plus a warp to a hub is the fast path. Copy lockstep: the
  frenzy has NO on-screen print since v17.46 (user 2026-09-04: "I dont want
  that display" — the "THE FRENZY" IPrintLnBold is gone; the mechanic is
  unchanged and unannounced). The ten TRIAL I..X banners LANDED in
  v16.25 (`trial_banner( tier )` at the seal — verified by the content-hash
  `.iwi` rule); **v17.69 retired 8..10 WHOLE (precache, zone, GDT, PNGs)
  and re-commissioned 1..7 with the new names + hall colours (docs/105,
  LANDED v17.70 the same night)**; the clamp in `trial_banner` reads
  `hub_laps().size`; the WON
  plate landed in v16.44 (`tod_trial_won`, `trial_banner( 0, "tod_trial_won" )`
  at the win). **THE GAUGE HAS A SPIRE MODE since v16.44 (docs/71)**: 35
  cells at pitch 30 since v17.69 (50 at pitch 21 for the 100-floor spire —
  LOCKSTEP TRIO: the slicer's spire profile, `SP_CELLS/SP_PITCH` in the Lua,
  `TOD_GAUGE_SPIRE_CELLS/LAPS` in the GSC; the docs/105 art LANDED v17.70 —
  cut with `--band-tol 140` because that delivery draws plates edge-to-edge,
  a documented override, not a green-by-number), a gold hub plate every 5th, the summit on top,
  a WHITE down tile —
  `_tod_gauge::gauge_mode()` reads `level.tod_spire_active` / `tod_spire_won`
  (never add a second latch); before it the bar sat full with the crown lit
  from spire floor 51 to 100. Both gauge sets are cut by
  `tools/slice_gauge.js` (profiles) from registered masters — a re-bake is
  one command plus a full build.

## Conventions

- Map name `zm_tower_of_doom`; script prefix **`tod`** (`_tod_*.gsc` modules,
  `tod_*::` namespaces, `level.tod_*` state) — mirrors the old map's `acc`.
- Entry scripts `scripts/zm/zm_tower_of_doom.gsc|.csc`; modules under
  `scripts/zm/zm_tower_of_doom/`; every module needs a `scriptparsetree` line in
  `zone_source/zm_tower_of_doom.zone`.
- **The `.map` is GENERATED** by `tools/gen_tower_map.js` from the layout tables
  at the top of that file. The generator ALSO emits
  `scripts/zm/zm_tower_of_doom/_tod_door_data.gsc` (door buy-trigger coords) so
  the .map and GSC can never drift. Regenerate BOTH with
  `node tools/gen_tower_map.js` after any layout change; hand-edits to the .map
  will be clobbered by a regen, so put changes in the generator.
- **DEV TEST HARNESS: REMOVED** (2026-08-25, verified 2026-08-26).
  `_tod_main::dev_crown_test` and the dev finale clock are GONE — the user had
  the throwaway harness reverted before publish (`_tod_main.gsc:63` records
  it). `level.tod_dev` still exists and still gates the money loop, early
  Panzer/boss intervals, 100% tier-card odds and unlimited station uses — but
  nothing warps to the terrace and the finale clock is the same 191 s in every
  build. If the ending needs testing again, write a fresh harness (recipe in
  the _tod_main comment: stock power entry
  `zm_power::turn_power_on_and_open_doors` + `zm_perks::perk_unpause_all_perks`
  — poking "power_on" by hand leaves perk machines paused — open every zone
  flag + the causeway gate, warp on spawn AND respawn), and remove it again
  before publish.
- Dev/test = ONE compile-time flag, `level.tod_dev` in
  `zm_tower_of_doom.gsc::tod_resolve_dev_flags()` (hardcode `= true;` +
  rebuild to arm a test session; ship state `= false;`). NEVER add dev dvars or
  tell the user to set console dvars — same doctrine as the old map (its
  CLAUDE.md "Dev/test mode" section).
- **Current test setup (2026-09-10, HARNESS #8 LIVE):** `tod_dev`, `tod_god`
  and `tod_dev_doors` armed (`tod_resolve_dev_flags`, unchanged since the
  floor-10 session) AND `_tod_main::init` threads `dev_spire_harness`: the
  draft runs, the round-1 deal clears, power on, every tower door open, the
  party ASCENDS with no finale, every spire door opens, and EIGHT WARP PADS
  appear — beside the arrival (-> hub 10) and on every hub's door landing
  (-> the next hub, 70 wraps to 10; refused mid-trial). Tier 3 + maxed comes
  from `dev_maxed_harness` (implied by `tod_dev`), not from #8. The warp lands
  you on the landing BEFORE the door facing the W flight (fixed 2026-09-10;
  it used to be the first tread past the door, facing back). Park #8 again
  (comment the one thread line) and disarm the flags before any publish.
  -GscOnly BUILD VERIFIED 2026-09-10 19:15:12 Eastern, FF 176,182,656 bytes; scripts/zone_source/ui diffs clean, nothing synced after the .ff; deployed _tod_main threads the harness and tod_dev/tod_god/tod_dev_doors read true. UNPLAYED.
- **Test setup history (2026-09-08, v18.57 — superseded by the bullet above):** `tod_god`, `tod_dev_money`,
  `tod_dev_doors` and **`tod_dev_altar`** are enabled in `tod_resolve_dev_flags`;
  `tod_dev` and `tod_dev_maxed` stay false, so the loadout is a normal tier 1 and
  upgrades are still earned. `tod_dev_altar` = UNLIMITED station buys at EVERY
  terminal, not just the spawn one (station_depleted; the not-scoped-to-spawn call
  is deliberate and its reasoning is at the flag). All four are caught by
  build_map.ps1:250, which refuses `-Publish` while any is armed. Read the live assignments
  before changing them; do not restore the earlier all-three-staff grant.

## PUBLISH PREP = BUILD + PATCH NOTES (user 2026-09-02)

**"When I ask for a full build for publish prep we need to generate patch
notes as well ... record the notes by day and time to be accurate."** The
Workshop item shipped 25 times without a single change note; that ends here,
and it is a GATE, not a memory: `build_map.ps1 -Publish` refuses to build
until `node tools/patch_notes.js check` passes.

The ledger `docs/publish_ledger.json` holds one row per Workshop upload —
upload time (machine clock, Eastern; Steam's page renders Pacific, +3 h),
`.ff` time, version label, and the NEWEST `CHANGELOG.md` header that upload
contained. Everything above that header is unreleased, and that is the window
the next notes cover. The player-facing notes live in `docs/68_patch_notes.md`
(one `## Update — <Mon D> (<version>)` section per upload, headings New /
Balance / Improvements / Fixes) with the same section as a paste-ready block
at the top of `docs/68_patch_notes_steam_bbcode.txt`. `docs/67_release_notes.md`
is the DEV history (every entry, condensed) — never paste that to players.

The flow, every publish, in this order:
1. Write the publish build's own CHANGELOG entry (it must be the TOP entry —
   the cutoff is captured from it).
2. `node tools/patch_notes.js window` → `docs/patch_notes_window.md`: every
   CHANGELOG entry newer than the last upload, with the clocks each recorded,
   plus the newest docs/68 section as the style reference. READ IT WHOLE.
3. Write the new section at the top of docs/68 and the BBCode file. Player
   voice only: no builds, versions, harnesses, "unverified", engine talk, docs,
   art prompts. Keep the numbers players feel. NET the window — a change made
   and undone inside it is dropped; a number moved twice reads old → final.
   Dev/test-only entries contribute nothing. `check` rejects bullets that
   carry dev vocabulary.
   **SHORT AND PLAIN (user, 2026-09-10: "reduce any jargon and make it super
   simple for players ... We dont need a billion characters for change
   notes"). ONE LINE PER BULLET, 200 characters at most — `stage` FAILS on a
   longer one (`MAX_BULLET` in tools/patch_notes.js) and prints the longest
   offenders.** Say WHAT changed, never how or why; group related knobs into
   one bullet instead of listing each; cut any second clause that only
   justifies the first. The Sep 10 2026 section is the reference — everything
   above it in docs/68 is the older, longer style, left as it went out.
   Reaching for the ceiling is a smell: that release covered a 16-entry
   window in 30 bullets, most of them under a hundred characters.
4. `node tools/patch_notes.js stage --version vX.Y` (heading date = today,
   or `--any-date`).
5. `.\tools\build_map.ps1 -Publish` — the gate runs `check`; after BUILD OK the
   script stamps the pending row with the `.ff` time (`built`).
6. **PASTE THE BBCODE BLOCK INTO THE CHAT, VERBATIM, IN A FENCED CODE BLOCK** (user 2026-09-13: "When i say prep
   for publish and get the patch notes I expect the patch notes to be pasted here in steam syntax so i can simply
   copy and paste" — pointing at the file is NOT delivery). Then the user uploads and pastes it into the Workshop change note.
   Then `node tools/patch_notes.js uploaded` pulls the Steam time, refuses if
   it predates the `.ff` (not uploaded yet), closes the row and writes the
   time into the docs/68 section line. If the session ends before the upload,
   the next session runs it — `status` shows a pending row.

⚠️ **`window` ONLY READS CHANGELOG.md, AND PEER SESSIONS DO NOT WRITE THERE (2026-09-16).**
The art sessions in this repo record in CLAUDE.md + docs/ and write no CHANGELOG entry, so a shared
day's work is INVISIBLE to the window and the notes ship short. v19.22's first cut missed ALL SIX
REBUILT HEAVENLY ALTARS and the reference one/two/three cyber roster - both already in the `.ff` -
and the user caught it ("What about the new altar look ... Did you miss stuff?"). **Before staging,
diff the tree as well as the CHANGELOG:**
`find scripts ui source_data localizedstrings sound sound_assets zone_source -type f -newermt "<the last uploaded row's .ff time>"`
and account for EVERY file it lists. A changed `source_data/*.gdt` or `model_export/` tree is a
player-visible art change even when no script moved.

**RECONCILE AGAINST THE LIVE PAGE BEFORE WRITING ANYTHING (2026-09-10).** A
PENDING row that outlives its own upload is the one failure no gate here can
catch: `stage` overwrites the pending row IN PLACE and `check` only compares it
to the CHANGELOG, so once an upload goes out against a row that stays pending,
every later `window` runs from a cutoff that is already public and hands back
bullets players have already read. That is how row #34 sat pending through the
Sep 9 v18.72 Mage release while the docs/68 section grew to 47 bullets mixing
shipped and unshipped work. NOTHING IN THE REPO CAN TELL YOU — ask the user for
the live Workshop notes (or fetch them) and match them against the last
**uploaded** row, never the pending one. One bullet dated that upload: "packed
staffs show EX after their name", which the next day's build replaced with the
true staff names. Fix = flip the row to `uploaded` with `confidence:
reconstructed`, split docs/68 so one section is exactly what players saw, and
stage ONLY at publish time so the ledger never carries a promise the Workshop
has not been given.

If the CHANGELOG moves after staging (a peer's entry, a late fix), `check`
fails on purpose: fold the new entries into the section if players would
notice them, then re-stage. `-SkipNotesGate` exists for an emergency and
prints a warning that the upload is going out without notes again.

## ART REQUEST PACKS = ONE DOC, ONE TOOL, ONE ZIP (user 2026-09-02)

**"Lets finalize this process of zipping up reference images and
instructions ... I can just send the zip to my asset generator and they can
easily know the task and goal."** Every baked-art request now goes out as
`~/Downloads/tod_<name>_art_pack.zip`, built by `tools/make_art_pack.ps1`
from a repo brief — never a hand-rolled zip, never a prompt pasted in chat.

- **The brief is a repo doc, `docs/NN_<thing>_art_prompt.md`, and it is the
  ONLY source.** It carries an `<!-- art-pack ... -->` header (`name:`,
  `refs:` = the CURRENT shipped files to match, each with a one-line role,
  `preview:` = the on-screen WxH) and a `<!-- PACK:BEGIN -->…<!-- PACK:END -->`
  section that becomes `INSTRUCTIONS.md` verbatim. docs/73 is the worked
  example; the tool's header documents the format.
- **INSTRUCTIONS.md is generator-facing:** deliverables table with EXACT
  filenames + sizes, hard rules, the exact text to bake, paste-ready prompts
  that name which `reference/` files to attach, a delivery checklist, a
  do-NOT list. No repo internals (the tool WARNs), no absolute paths (the tool
  FAILS — a generator cannot open `C:\` anything).
- **The tool** copies the refs to `reference/`, writes `reference/README.md`
  from the roles, renders every PNG ref at its real on-screen size into
  `preview_onscreen_<WxH>/` (what the player sees is what the generator
  should judge against), checks PNG headers, and zips. Run it after EVERY
  edit to the doc — the zip is a build product, the doc is the source.
- **EVERY PACK CARRIES OUR TYPEFACE (user 2026-09-25: "any text or symbols on the
  assets should use the typography that we provide").** The tool always adds
  `typography/` (both `_sheets/` font sheets + `art/typeface/specimen.png` + a
  character list) and appends `tools/art_pack_typography.md` to INSTRUCTIONS.md.
  `typography: off` in the header ONLY for a brief that redraws the face itself.
  Proofread every drop's baked text against the glyph set (A-Z 0-9 - ' . / + coin).
  **THE FACE IS docs/172 OPTION A "TOWER 1 REFINED" since 2026-09-25**; the TOD1
  originals are kept in `art/typeface/tower1_original/`. **THE CLASS ART THEME IS
  docs/171 THEME B "FALLEN / BLACKOUT"** (Skirmisher installed 2026-09-25; the
  other four requested in docs/173). ⚠️ `slice_hud_sheets.js` re-cuts EVERY sheet:
  it overwrote the hand-fixed loose `i_tod_hud_gun_mac10/stoner63.png` — after any
  slice, `git status` the gun icons and restore any the sheet did not mean to change.
- **The drop** comes back as `~/Downloads/files (N).zip` (newest N; often the
  PNGs loose AND a nested zip). `.\tools\make_art_pack.ps1 -Inspect
  'files (N).zip'` extracts it (nested zips too) and prints size / colour
  type / md5 / whether a same-named repo image exists and differs. It
  installs NOTHING: LOOK at every image, proofread baked text, overlay
  against the shipped file, then copy into `source_data/tod_ui_images/_images/`.
  Same name = no wiring; new name = GDT block + zone `image,` line + Lua slug.
  FULL build always; proof = a fresh content-hash `.iwi` beside an untouched
  control. Flip the doc's STATUS to SHIPPED with the build version.

## Match the effort to the question (user 2026-08-28)

**"Why is it taking a whole research team to turn a machine model?"** — a fair
callout, and the rule now: **DO NOT spin up a multi-agent workflow for a
question with one small answer.** Rotating a model is one number. Four
research agents plus verifiers to find "-90" is waste, and it delays the fix
past the point the user could have just looked at it in game.

The test before delegating: *how many distinct places must be read, and what
does being wrong cost?*
- **One number / one file / one obvious call site → just do it.** A wrong yaw
  costs one 4-minute `-GscOnly`. That is cheaper than the research.
- **Reversible + instantly visible in game → prefer shipping a guess** over
  proving it on paper. The user testing IS the measurement, and they are
  faster at it than any parser.
- **Fan out only when the answer genuinely lives in many places at once** —
  the map-wide trigger/UI-copy audit was the right call (5 systems x every
  runtime state, 32 findings, one of them a live regression nobody would have
  found by reading one file). Sweeps, audits, and "what did we miss" earn it.
- Never let a running workflow become the reason a known-broken thing sits
  unfixed. If the fix is obvious, ship it and let the research land later.

TWO AXES, NOT ONE (both-sessions postmortem, same night). Scale the WORK to
cost/reversibility — but never scale down the CHECKING of a factual claim.
The same evening produced both failures: research prices paid for a one-number
yaw (over-delegation), and a confident "there is no crown PaP" told to the
user off a name-grep while the emission site sat open in the editor
(under-checking). A wrong yaw reverts with one build; a wrong CLAIM
propagates into what people believe and act on, and does not revert.
**CHEAP TO CHANGE IS NOT THE SAME AS CHEAP TO BE WRONG ABOUT** — before
asserting what the code does or contains, read the site that produces it.

## Dev-mode diagnostics for feature work (user 2026-09-10)

**Make useful dev logs a normal part of building features and fixing bugs.**
For most gameplay features, stateful UI features and substantive fixes, include
enough diagnostics that a normal dev-mode playtest leaves evidence another
agent can use. The user should not have to repeat a session just because the
first implementation recorded nothing useful. Scale this to the change: a
static text or art edit usually needs no new instrumentation.

- **Run automatically with dev mode.** Gate server diagnostics on the existing
  `IS_TRUE( level.tod_dev )`; use the established dev/logging channel for the
  relevant VM. No extra feature toggle, console command or special user action
  should be needed. Keep useful diagnostics with the feature for future tests.
- **Log decisions and outcomes.** Prioritize initialization, important state
  changes, activation/completion, denied actions with their reason, timeouts,
  failed lookups and cleanup/restoration. Include a consistent feature tag
  such as `[TOD_TELEPORT]`, game time, relevant player/entity identity, and
  the values needed to explain the decision. For example: resource before/after,
  cooldown remaining, requested destination/result, or expected/actual state.
  Include an operation or lifetime identifier when events can overlap or an
  entity slot can be reused. Avoid context-free messages such as "failed".
- **Record at the source of a transition.** A periodic snapshot can miss an
  entire operation between samples, as the same-frame elite pause did. Log or
  stamp critical writes and their matching release/completion at the actual
  call sites. Trace both sides of a server-to-HUD handoff when that handoff is
  what needs diagnosing, using each VM's supported channel.
- **Keep logs cheap and separate from gameplay.** Prefer changes/events over
  per-frame output; throttle repeated failures and use bounded summaries for
  loops or large collections. Diagnostics must not change targets, goals,
  timers or gameplay state, invoke callbacks with side effects, or introduce
  a growing history in memory. Guard missing/deleted entities. Use the console
  log rather than player chat, floating text or a debug overlay by default.
- **Verify that the useful records actually appear.** Compilation alone does
  not establish that a logger runs. During the authorized native test, check a
  startup/revision marker and representative success/failure or state-change
  records with populated fields. If a path could not be exercised, say so;
  do not claim that every diagnostic branch or the whole feature was tested.
- **Preserve and explain the evidence.** Use the existing launcher/capture
  workflow before relaunch. Search the raw archived console by the feature tag;
  the filtered extract includes uppercase `[TOD_*]` feature tags as well as
  AI/native errors. Extend it when needed. Record the tag, important
  fields and capture location in the feature's notes so the next agent can
  read a user's completed playtest without rediscovering the instrumentation.

For server GSC, use the proven PrintLn pattern below inside the feature's
existing module; do not import an unrelated gameplay module just to log.
The module needs its usual `shared.gsh` insert for `IS_TRUE`.

```c
function dev_log( msg )
{
    if ( !IS_TRUE( level.tod_dev ) ) return;
    line = "[TOD_FEATURE] ms=" + GetTime() + " " + msg;
    /#
    PrintLn( line );
    #/
}
```

Replace the example tag with the feature name. **Assemble the full string
outside the developer block; keep PrintLn inside it.** The native loader
rejected an unwrapped call despite a successful compile, and literal strings
assembled inside the block were blank in a tested run. The existing launchers
already supply `developer 1`, `logfile 2` and `scr_mod_enable_devblock 1`.
Follow [docs/132_native_game_verification.md](docs/132_native_game_verification.md)
for native verification and log preservation; diagnostics do not waive the
rule against rebuilding while the game is running.

## Agent-operated native game verification (user 2026-09-10) — ONLY WHEN ASKED (2026-09-16)

⚠️ Read the top of this file first: the user tests, the agent writes logs.
This section is the recipe for the case where the user explicitly asks for
an agent-run match in that message; it is not a standing authorization.

**Build and start authorized test matches yourself.** The user explicitly asked
that both Claude and Codex know how to do this, instead of handing launch steps
back to them. Follow [docs/132_native_game_verification.md](docs/132_native_game_verification.md):
`tools/run_game.ps1` launches through Steam with the correct gametype and devmap,
archives the old console, and enables the actual developer-block logger. Use
`tools/focus_game_window.ps1` and `tools/game_window.ps1` to focus, inspect and
click Steam's custom-arguments Continue dialog, then inspect the native game
and logs. Handle that dialog yourself for an already-authorized launch. A
process or a memory-threshold message is not proof that the map loaded.

Never build while BO3 runs. Do not interrupt an active user match without their
okay. The user judges subjective visuals/gameplay; agents handle builds,
launches and objective native checks. Check every helper's exit code, use DPI-
correct window-relative coordinates, and stop input if focus fails. Do not use
unguarded SendKeys or type console commands as player chat. Preserve logs before
relaunch and report whether the final build was actually tested in game.

## Build / run (same pipeline as the old map)

- `.\tools\build_map.ps1` — full headless build (sync → cod2map64 [cwd=bin] →
  Radiant LED bake → linker → verify fresh `.ff`). `-GscOnly` for
  GSC/.zone-only changes. **Build it yourself; the user's job is to TEST.**
  Build success = a FRESH `.ff`, NOT the linker exit code.
- **THE XPAK IS APPEND-ONLY — CLEAN IT BEFORE EVERY PUBLISH (2026-09-03,
  docs/86).** The linker never removes anything from `zone\<map>.xpak`: every
  full build leaves the previous build's reflection probes / probe volumes /
  sun-shadow tree behind under the SAME names, every replaced asset leaves an
  un-indexed hole, a retired asset keeps its entry. Measured that day: a 9.5 GB
  pack of which ~5.3 GB was history (47 shadow trees under one name, 221 probe
  sets for 55 probes, 1.4 GB of holes), and that pack IS the Workshop download.
  `-Publish` implies **`-CleanPak`**, which now rebuilds ALL main/language packs
  and implies `-AllLanguages` (moves packs out of `zone\`, preserves old FFs/
  banks until every language passes, restores on failure; `-KeepPak` opts out).
  `last_payload.json` beside `zone\` records the complete final folder size.
  **Answer any
  size question with `node tools/xpak_report.js`** — it reads the pack's own
  index and attributes every byte; docs/61 #8 reasoned from the asset list and
  was wrong by 5 GB. Our `i_tod_*` UI art is NOT in the pack (it rides the
  `.ff`), so its `uncompressed` setting is not a lever **FOR DOWNLOAD SIZE**.
  ⚠️ **IT WAS AN ENORMOUS LEVER FOR RESIDENT RAM, AND THAT COST WENT UNSEEN FOR
  MONTHS BECAUSE THIS SENTENCE READ AS "not a lever" FULL STOP (fixed v19.8,
  2026-09-14).** Uncompressed art is cheap on disk (LZ4 inside the `.ff`) and
  ruinous in memory: it expands to raw RGBA8, and 731.0 MiB of the map's 920.6
  MiB resident was `i_tod_*` UI art — 79.4%, of which 596 MiB was 177 upgrade
  cards at 3.38 MB each. Flipping the div-4 ones to `compressed high color`
  (BC7, format byte 0x1f — NOT the DXT5 that v16.97/docs/89 object to) took the
  map to 377.8 MiB. **DISK SIZE AND RESIDENT SIZE ARE DIFFERENT QUESTIONS WITH
  DIFFERENT LEVERS; `xpak_report.js` answers the first and the linker's
  assetinfo ledger answers the second.** Tools: `set_image_compression.js`
  (`--restore`) and `verify_image_compression.js`. Third-party texture
  RESOLUTION is: `tools/downscale_pack_textures.js` caps a pack's sources with
  the originals parked in `<modtools>\_tod_texture_originals\` (`--restore`
  undoes it); the nine sold perk machines were capped at 1024 that day.
- **KEEP THE BUILD SMALL — IT IS A GATE NOW, NOT A GOOD INTENTION (user
  2026-09-03: "keep this process of minimizing the build ... we somehow had
  7GB of random stuff not even used").** The item went 9.61 GB → ~2.4 GB in a
  day, but **be accurate about where it went**, because the three causes have
  three different fixes and only two are automated:
  (1) **build history inside the pack — ~5.3 GB, the bulk of it.** The linker
  APPENDS to `zone\<map>.xpak` forever. Fixed by `-CleanPak`, implied by
  `-Publish`. Prove with `node tools/xpak_report.js`.
  (2) **texture resolution on assets the map DOES use — ~1.2 GB.** Perk
  machines at 4096², the Leviathan axe's uncompressed TIFFs, the riot shield's
  13 materials at 2048². Fixed per-pack with
  `tools/downscale_pack_textures.js --cap N <gdt> --apply` (originals in
  `<modtools>\_tod_texture_originals\`, `--restore` undoes it). NOT automated —
  it is a judgement call about how close a thing is ever seen.
  (3) **genuinely unused assets — only ~130 MB**, and that is the honest
  number: the Street Sweeper (a retired class's gun), the Mahem rocket (a
  function with no caller), 12 cards for retired domains. Hunt them with
  `node tools/audit_zone_usage.js` (reads "computed? prefix" as USED — perk
  cans, `_up` PaP forms and `_on` machine models are all built at runtime).
  **`tools/lint_tod_assets.js` now gates the recurring case on every build**
  (see the UI-art lint bullet below).
  **THE RULE THAT KEEPS IT SMALL: when you retire anything, retire it whole.**
  A domain is its `add_domain` AND its `CARD_SLUG` slug AND its card zone
  lines; a weapon is its zone lines AND its alias rows AND any script lane that
  named it. Half a retirement is either dead weight (art with no code) or a
  WHITE SQUARE (code with no art). Five domains were retired half-way before
  anything checked. **And never delete on a name-grep alone** — read the site
  that would use it: the gift gun looked unused because nothing calls
  `GiveWeapon` for it (it is the Death Machine powerup, redirected through
  `level.zombie_powerup_weapon`), while the Mahem rocket looked used because
  its function existed (nothing had called it since 2026-08-20). Full record
  and the numbers behind every claim: `docs/86_xpak_size.md`.
- **UI ART LINT — `tools/lint_tod_assets.js`, runs on EVERY build incl.
  `-GscOnly`** (both its failure modes are pure zone/Lua edits). GATE A, hard
  fail: an image a live path names with no `image,` line — the linker is silent
  and the game draws a WHITE SQUARE. GATE B, gated on regression against
  `lint_tod_assets.baseline.json`: a `CARD_SLUG` slug whose domain is dead, a
  zoned card no slug declares, a dead pause plate. Cards are `uncompressed`
  768x1152, so **one dead card is 3.4 MB of LOAD RAM** — that, not disk, is why
  this matters. The baseline's `why` block records which current numbers are
  accepted (the 10 retired-domain pause plates are deliberate, ~0.5 MB) —
  **never raise a number to make it green.** It parses `domain_id`,
  `add_domain`, `CARD_SLUG`, `CARD_ONE_IMAGE` and `PAUSE_PLATE_MAX` out of the
  live sources, so renames follow automatically. It does NOT model materials,
  GSC-only image refs, or names built from tables it does not read — a pass
  means the modelled lanes agree, not that every image is reachable.
  `tools/lint_tod_assets_selftest.js` breaks the map eight ways (six that must
  fire, two shapes that must not) — run it whenever the lint is edited.
- **THE SUN VOLUME MUST NEVER SHRINK BELOW `SUN_VOLUME_TOP_MIN` (v17.80,
  2026-09-05, docs/107).** `SKY_TOP` in the generator sizes the sky seal AND
  the `volume_sun` brush (the map-wide sun / light-grid volume) as a `max()`
  over the tallest geometry. When v17.69 cut the spire from 100 to 70 laps
  the crown took over, the volume dropped 39,468 → 29,196, and THE WHOLE
  TOWER LIT YELLOW-OLIVE — every surface, the viewmodel, the zombies — on
  default light parameters (light positions honoured, colour and lighting
  state not). Six builds of sky / fog / light / flag reverts changed nothing
  because none of those had changed; the published build had the tall
  volume by accident. Confirmed by a bisect the user looked at both ways;
  the bake's `.led` size is the fingerprint (45,041,494 B good, 44,592,07x
  yellow). The floor is an extra `max()` term; the generator prints
  `ceiling` on every run — 39,468 is right. **When every direct lever fails,
  diff the DERIVED numbers against the published build** (its pack and `.ff`
  are on disk under `steamapps\workshop\content\311210\3788921059`), and
  build the control map (`Repositories\test+map`, the Mod Tools template,
  one look) FIRST, not sixth. Radiant is a GUI exe: `Start-Process -Wait`
  it, or the linker links without a `.led` and prints "Falling back to
  preview lighting".
- **LED bake is a gate** after any geometry change — `tools/_bake_test.ps1`
  prints BAKED/CRASHED (the brush.cpp:1860 lightmap-atlas ceiling; see KB §1).
  **READ IT AS BAKED/CRASHED AND NOTHING ELSE.** Its TIMING is not a budget
  meter: on near-identical input this map has come back 38.2, 126.2, 35.1, 31.9,
  31.3 and 31.8 s — a 4x spread, and the 126.2 was a one-off that never
  reproduced (an A/B with byte-identical geometry ruled out the material
  distribution as the cause). Timing here is dominated by HOST STATE. A single
  bake reading justifies NOTHING; if a number is going to decide something, bake
  twice and A/B it. For the actual budget question run
  `node tools/measure_lit_area.js` — deterministic, instant, and it groups lit
  area by region so you can see what changed (the crown was 67% of the map's on
  2026-09-14 — RUN THE TOOL, the share moves whenever either tower changes).
- **Two ADVISORY crown tools** (not gates, but run them after any crown edit):
  `node tools/measure_lit_area.js` groups lit surface area by region — the crown
  was **67%** on 2026-09-14 (949M of 1409M u²), not the 84% this brief claimed
  for months; that figure predates the spire, which both diluted the share and
  shrank the crown itself. Run the tool rather than quoting a number.
  ⚠️ **AND IT IS A LIGHTMAP-BAKE / VRAM FIGURE, NOT A PER-FRAME DRAW FIGURE** —
  the tool says so in its own header. It was cited as evidence about a runtime
  GPU hang during the 2026-09-14 freeze investigation and answers no such
  question. `node tools/audit_hidden_faces.js` samples every face and
  reports what nothing can see; it found panel stiles, jewel bosses, a keystone,
  an arch segment and the mouth jambs all sealed inside other brushes. Two cases
  are always wrong: buried on ALL SIX faces (pure cost), and a visible face
  COPLANAR with a neighbour in another material (a z-fight). Everything else is
  advisory — a tenon keyed into a wall is supposed to be buried.
- **NOTHING MAY STAND ON THE CAUSEWAY.** The J4 landing is 960 wide (x +-480,
  y 6720-6880 at TOP2) and the crown face is 32 north of it, so anything pushed
  proud lands on walkable deck. NO LINT CATCHES THIS — the misplaced-wall check
  only fires on `clip` with no visible solid, a VISIBLE solid silently drops the
  node, and the flood still walks the middle of a 960-wide landing. gen_tower_map
  section 5f.9 asserts it against the emitted brushes; keep that assert.
- **`tools/lint_tod_geometry.js` is the other geometry gate** — HOLES and
  MISPLACED WALLS, run automatically by `build_map.ps1` before cod2map. Proves,
  whole-map in ~1 s: no invisible blocker where a player stands, no unguarded
  edge, and base→terrace + terrace→citadel still walkable. Gates on REGRESSION
  against `tools/lint_tod_geometry.baseline.json` (currently zero of
  everything). `tools/lint_tod_geometry_selftest.js` breaks the map six ways and
  requires the lint to catch each — run it whenever the lint is edited.
  **If it goes red on a map somebody has WALKED, suspect the lint** (that
  happened twice the day it was written and both times the check was wrong, not
  the map). Never edit the baseline to make it green. It cannot see
  script-spawned collision, prefabs, or the navmesh.
- **IS THE `.ff` ACTUALLY BUILT FROM THIS TREE?** Three different freshness
  checks have now been trusted and been WRONG, so use this one and only this one:
  ```
  diff -rq scripts     <modtools>/usermaps/zm_tower_of_doom/scripts
  diff -rq zone_source <modtools>/usermaps/zm_tower_of_doom/zone_source
  diff -rq ui          <modtools>/usermaps/zm_tower_of_doom/ui
  ```
  (ignore the generated `all/`, `english/`, `loc/` output dirs). Empty = the
  linker consumed exactly this source. The `ui` line was added 2026-08-30
  (v14.18 postmortem): Lua rides in `ui/` as zoned rawfiles, so a Lua-carrying
  change was invisible to the old two-line check — scripts/+zone_source/ clean
  proved nothing about it (sync_to_modtools.ps1:159 mirrors ui/, so it was
  never at RISK, but the doctrine check must COVER what it claims to prove).
  **Do NOT "improve" it by adding
  map_source/** — after any `-GscOnly` the sync makes deployed .map == repo
  .map while the `.ff`'s compiled BSP is a regen behind, so a map_source diff
  passes exactly when it should fail (live 2026-08-28: a `-GscOnly` synced the
  615-entity .map while the `.ff` geometry was still the 611-entity compile;
  the spur risers were "deployed" and absent). scripts/ + zone_source/ + ui/
  is the whole sanctioned check for SOURCE; geometry freshness
  is proven by the FULL build's own regen-count print, nothing else.
  **BUT THAT DIFF ANSWERS A QUESTION ABOUT THE LAST *SYNCER*, NOT THE LAST
  *BUILDER*** (added 2026-09-01, three sessions in one repo). The sync runs at
  the START of a build, so the deployed tree always reflects whoever synced most
  recently. The moment a peer starts a build, deployed == THEIR repo state, the
  diff goes green, and it is now reporting on *their* build-in-progress. Live
  that day: a clean diff was nearly read as "my build consumed this tree" when a
  peer's sync 90 s earlier had already replaced the deployed tree, function
  rename and all. **Pair it with a check that nobody synced after your `.ff`:**
  ```
  find <deployed>/{scripts,ui,zone_source} -type f -newermt "<your .ff timestamp>" \
    | grep -v -E "/all/|/english/|/loc/"
  ```
  Empty = the diff is about YOUR `.ff`. Non-empty = you are reading someone
  else's answer and your verification is **VOID, not passing**. The two are
  COMPLEMENTARY and you need both: the diff catches repo != deployed (an edit
  never synced, or the mid-build edit below), while the `-newermt` catches the
  case a peer's sync would otherwise HIDE — because that sync sets repo ==
  deployed and turns the diff green over everything.
  **AND EMPTY IS NOT ENOUGH WHEN A PEER BUILD IS RUNNING (2026-10-02 21:39): the
  sync PRESERVES SOURCE MTIMES**, so a file a peer edited after your sync but
  before your `.ff`, deployed by THEIR later build, is OLDER than your `.ff`:
  `-newermt` misses it and the diff goes green over their tree (the Dealer
  voice, 21:32 edit, 21:36 peer sync, both checks clean). Also list the REPO
  files modified after your build's start (`find scripts ui zone_source ...
  -newermt <build start>`): those are NOT in your `.ff`, whoever owns them.
  **An mtime gate cannot answer this**:
  `build_map.ps1` SYNCS AT THE START, so a file edited mid-build is older than
  the `.ff` and newer than the sync — a peer edit 25 s before the `.ff` was
  written was not in it, and `find -newer` called the tree clean.
  And "synced" is not "packed": **a `.gdt` edit is ALWAYS a full build.** The
  MECHANISM claim that used to live here ("-GscOnly runs no gdtdb /update") is
  WRONG for today's script and was corrected 2026-08-30 (v14.16 publish, 87's
  live observation + verified in build_map.ps1: the gdtdb step at ~:226 runs
  on EVERY build, before the -GscOnly branch at :282, and image assets
  demonstrably converted during a -GscOnly). The rule survives on the still-
  true grounds: -GscOnly skips cod2map64 + the LED bake, so anything a GDT
  feeds into the BSP/lighting (materials, model surfaces) links against a
  stale compile — and per-asset conversion coverage under -GscOnly is
  UNPROVEN, not proven-safe. Full-build after GDT edits, same as ever; just
  don't cite the gdtdb line as the reason. (Contrast door PRICES, which
  really are `-GscOnly`.)
- Launch: `PLAY_NORMAL.bat` or `.\tools\run_game.ps1` (steam://run/311210 +
  `+set_gametype zclassic` — the ONE load-bearing arg; never raw exe, never
  Steam Launch Options).
- Mod tools root: `...\Call of Duty Black Ops III 455130` (detected via
  `bin\modlauncher.exe`). Linker builds the DEPLOYED usermaps copy — sync
  before every build (build_map.ps1 does it).

## Hard-won facts inherited from map 1 (the short list — full set in the KB)

- Map-authored `zombie_door` trigger_use entities are DEAD for generated maps —
  `_tod_doors.gsc` disables them and spawns `trigger_radius_use` on BOTH sides
  of each doorway (script-spawned use-triggers need `TriggerIgnoreTeam()`).
  Buy = charge points, set the zone script_flag, hide+notsolid+connectpaths the
  slab. Slab starts `solid(); disconnectpaths();`. **THE ANTI-VAULT CLIP OVER
  A DOOR RIDES IN THE SLAB ENTITY (v16.13)** — a worldspawn clip is permanent
  and outlived the purchase: players jumping down a flight hit "an invisible
  wall above where the door would be" for the rest of the match (both towers,
  153 doors). A clip that must vanish with the door is a second brush of the
  script_brushmodel, never a worldspawn brush.
- GSC dialect: `function` keyword, `#using` before `#namespace`, `#precache`
  only AFTER every `#using`/`#insert` (misplacing it IS a compile kill, live
  2026-08-20 — but **"No generated data for '<file>.gsc'" is NOT a
  precache-specific message**, corrected 2026-08-31: it is what the linker
  prints for ANY compile failure in that file. A dangling variable reference
  produced it verbatim that night. Read it as "this file failed to compile,
  cause unstated" and diff the file against its last building state — never
  as "your #precache is misplaced", or you will audit the one thing that is
  fine. Note `lint_tod_arity.js` PASSES a file with this class of error: it
  checks call arity and symbol resolution, not variable liveness, so the
  linker is the only gate that catches it), ternary fully
  paren-wrapped, no `.field` on parenthesized expr, `class` reserved,
  `"power_on"`/`"initial_blackscreen_passed"` are FLAGS (`flag::wait_till`),
  never write `player.score` (use `zm_score::`), read-only damage callbacks
  MUST `return -1`.
- Navmesh ignores ALL entity collision → any script-spawned solid needs
  `DisconnectPaths()` (and `ConnectPaths()` when cleared).
- Playable space below z=-1000 triggers the stock below-world zombie failsafe —
  this tower goes UP, so not an issue here.


## Cybercity realistic material kit (2026-09-25)

The user chose MORE REALISM for Tower of Doom II, then explicitly expanded
this work from a shop bay to THE ENTIRE CROWN SECTION: "Dont miss a spot."
The complete detached island now uses the authored kit: 803 world solids,
8,634 faces, plus the crown gate. Interior, outside shell, underside, points,
arches, jewels, hanging ornaments, approach, balcony, passage and overlook.
The tower outside that island retains the peer's current blackout materials.

Read docs/art_cohesion/README.md and review.html. Blender MCP sources are
art/cybercity_materials/cybercity_material_library.blend and
crown_surface_library.blend: six modeled tile sources, eleven reusable source
materials, thirty baked maps. New Blender props should reuse this material
language. Interior tiles are 128 units; large exterior armor 512; crystals 256.
Native palette/finish roles: tools/art_cohesion/crown_materials.json and
surface_definition.py. The exterior is subdued metal/brass/colored glass,
not the inherited saturated toy-gold/primary-jewel palette. World scaleRGB is
ZERO to respect the blackout/power-wave request; native powered lights reveal it.

The generator calls crown_surfaces.js before the global blackout remap; it
covers WORLD AND ENTITY brushes and the two pendants below z=14000. Do not
change shared MAT.crown* directly: the spire uses those too. verify_crown.js
rejects any old materials left on the island and compares actual convex planes
against crown_before_refactor.json. Floor/wall use their original whole solids,
checked by verify_geometry.js. No new roof/collision or gameplay changes.
Stock perk/lever/crate models remain; authored shop/teleporter/altar designs and
state colors remain. crown_complete.blend is the actual architecture in Blender
with native hero meshes at their map anchors; its render uses review lighting,
not native lighting states, and omits stock props/runtime FX.

profiles.py owns prop satin finishes: shop unchanged; teleporter ready/off
max gloss 13 -> 8 with shop spec/probe settings; altar 6 -> 5 retaining highlights.
Never restore the old preview tricks (TP metallic .7 ignoring gloss range;
altar forced .65-.9 roughness). native_preview.py reads maps, gloss range and
native sRGB material tints, but is an APPROXIMATE fullspec/GGX view, not BO3
BRDF/probe/exposure parity. Native visual approval remains the user's test.
Original prop masters and geometry remain intact.

A FULL guarded build is required. verify_surfaces.py, verify_geometry.js and
verify_crown.js are build gates. Snapshot verify_deployment.py --snapshot just
before building, then run it after a fresh FF to prove matching deployed inputs,
eighteen packed crown wc materials, twenty-five used tile images and database
settings. Never sync over another build or user match. Build status: complete
crown FULL build passed September 25, 2026 (FF 206,925,056 bytes at 11:20:25
local). Deployment verification passed: 403 source inputs, 18 packed world
materials, 25 used images and 23 native finish definitions. No game launched;
native visual playtest pending. Evidence: art/cybercity_materials/deployment.json.
Post-build coordination: the separate sky session replaced its EXR at 11:21:56
and started FULL build tmp/sky3d_build/full_build_v6_112313.log at 11:23:13.
Only that source differs from our captured inputs; crown art remains unchanged.
Wait for that build before playing. Our strict deployment verifier intentionally
rejects that newer source tree against the earlier snapshot; do not waive the
guard or overwrite the old snapshot to claim the new sky was in our build.
Review update: docs/art_cohesion/review.html now shows before/after side by side
with four matched views and standalone image exports. Before is reconstructed
from the recorded blackout-era assignments and finish_before.json, not a game
screenshot. Both sides share geometry, lights, exposure and crown_views.py
cameras. Reproduction: 10_render_before.py + 11_export_comparisons.js. Preview
only; the finished master and native inputs were not changed by this comparison.

**2026-09-25 — CHARCOAL HORDE + TWO ROUND ELITES (user request supersedes the
earlier regular-horde choice):** ordinary zombies now use the Hellbound charcoal
character under `archetype_tod_charcoal_zombie`, selected by the historical
`tod_cyber_dev` factory marker in every mode. Gray/black/red only: grayscale skin
maps, red-only eye albedo/emission and pure-red material tints; native head and
gib assets share those bindings. Do not restore the original orange eyes.
`_tod_cyber_elites.gsc` is the sole normal-round owner for black robotic-legged
Doppelgasts and DEFAULT Hellbound Manglers. `tod_only_zombies` remains true to
keep all older directors disabled; the requested pair is the explicit exception.
Introductions round 3/5, then budgets 1/2/3 at rounds 6/14/22; 25 active seconds
between deliveries, two alive, existing shared roof and actor reserve respected.
Robot geometry/textures were authored through actual Blender MCP, preserving the
Doppelgast skeleton, upper body and original eyes. Source and compiled coverage
gates live in `tools/cyber_elites/verify_assets.py`; the shipping director is
exercised by `tools/test_cyber_elites.js`. Details, preview and diagnostics:
`docs/cyber_elites/README.md`. Build evidence: `art/cyber_elites/deployment.json`.
The user tests; native visuals/gameplay remain unverified until their playtest.
Final full build PASS: FF 209,794,304 bytes, fresh LED 150,000,159 bytes, compiled
triangle coverage for all 15 custom models and default Mangler, eight existing
known-waived warnings. All deployed inputs match; no post-FF sync. Three donor
charcoal limb references are corrected in the private GDT: legDmg2 -> g_rlegoff,
leftarm_gibmodel -> s_larmspawn, leftleg_gibmodel -> s_llegspawn. The source gate
checks these so retained-body geometry cannot be used as a detached limb again.

**2026-09-25 13:07 user run — MANGLER GENERIC-TREE LOAD FAILURE:** the 12:26
roster build passed the linker but failed runtime server load with `animation
'hb_mangler_cannon' not defined in anim tree 'generic'`. Archive:
`tmp/elite_tracking/runs/20260925_130758_272_059e6e76/console_mp.log` lines 3568–3581.
The .zone already packed the clip; `animtables/hb_mangler.ai_am` omitted it.
Added `anim_zombie_mangler_cannon,hb_mangler_cannon` to the map-owned table and
the donor import procedure. `test_cyber_elites.js` now checks every scripted
%clip in BOTH elite modules against the mapping table, with a negative control
that removes the cannon row. A successful link/xanim ledger row alone does not
prove generic-tree membership. Do not edit the shared stock tree. Build evidence
for the correction: `art/cyber_elites/animation_fix_deployment.json`.

### 2026-09-26 - Crown alarm / Doppelgast Blender pass (native build passed)

User: real red-only rotating alarms on every crown pillar, center, and top point;
then fix missing robot leg textures, finish both. Blender MCP authored 30 physical
fixtures and repaired the 152 robot parts with 12 real maps + UVs. Original enemy
rig/body/eyes retained. Native build passed 14:36:13 Eastern, FF 189,911,680 bytes,
using build 7's full geometry/LED and tmp/crown_alarm_final_relink.log. All nine
alarm LODs, spotlight FX, twelve leg maps and Mangler cannon mapping are compiled.
277 alarm/shared and 341 elite/shared hashes match; nothing synced after the FF.
Eight existing waived warnings remain. Handoff: docs/crown_alarm/BUILD_HANDOFF.md.
The standard build checks lifecycle, source materials, compiled LODs and root FX.
Review: docs/crown_alarm/review.html. Logs: [TOD_CROWN_ALARM]. No game launch.

2026-09-26 crown/legs follow-up: build 7b reported OK but the post-build asset
ledger audit found the crown spotlight missing (native MatchToken / Unknown
editor elem). Fixed 02_integrate.py's multiline name replacement; preserved
all native light fields, added a negative control and required the root FX in
verify_native.py. The EFX-only guarded relink succeeded; the spotlight root asset
is now present, the parser error is gone, and a deliberately missing-FX ledger
fails the new gate. Evidence: art/crown_alarm/deployment.json and
art/cyber_elites/leg_texture_deployment.json. No game launch; user test pending.


### 2026-09-26 - Color restoration + subtle powered wires (SOURCE READY, UNBUILT)

User: the migration lost the old map's colors; restore color/contrast, and add
subtle wiring inside floor/wall surfaces that glows only after power. This
supersedes the September 25 muted crown palette: the same authored surface kit
now has cobalt floors, violet wall panels, warm gold and richer jewel roles.
All world emission stays zero. Thirty source tile maps, collision, geometry,
lighting/exposure/sky, prop finishes, zombie palette and alarm art are unchanged.
Power wires are 70 tiny nonsolid off/on model twins (50 floor, 10 tower parapet,
10 crown/hallway), with emission restricted to two fine cyan conductors. The
persistent power flag owns their state; the crown alarm module only bootstraps
them. The existing art package/sync covers the new files. Actual source state
and placement tests pass; automatic [TOD_CONDUIT] READY / ON / SPAWN_FAILED logs.
Review: docs/art_cohesion/review.html; details: COLOR_RESTORATION.md there. Models
were authored and all three previews assembled through Blender MCP on port 9883.
FULL build/LED required; NONE run or synced. Build request/status in
 docs/crown_alarm/BUILD_HANDOFF.md. Waiting for Archer lead clearance (per the
updated AGENTS.md), or the user's explicit override. No game launch.

### 2026-09-26 alarm intensity follow-up (Blender agent; source ready, unbuilt)

User playtest: alarm lights feel weak. Archived console at
`tmp/elite_tracking/runs/20260926_153852_841_a5eddc36` confirms 30 fixtures and
13 hall spots activate. New owned profile `tools/crown_alarm/light_profile.json`
sets intensity 1800 (was 450), reach 900 (360), FOV 78 (62), lamp emission 36
(12). Geometry analysis: the old horizontal cones cannot reach the hall floor;
all 13 new cones can. Native shading/appearance remains a user test.
MCP updated the lamp master and matched hall/motion review; see
`docs/crown_alarm/INTENSITY_PASS.md` and `review.html`. Nine model files and all
28 images are unchanged. Runtime ON log records the tuning; lifecycle, radius
bounds, floor reach, source assets, script arity/API checks pass.
NO build/sync or game launch. Joins the color/conduit FULL build request in
`docs/crown_alarm/BUILD_HANDOFF.md`, awaiting Archer clearance per AGENTS.md.
Run both the color and alarm deployment audits there after the cleared build.
Teleporter gloss/pink follow-up remains pending its requested screenshot;
no teleporter material was changed during this follow-up.

### 2026-09-26 alarm starting phases (Blender agent; source ready, unbuilt)

User wants random starting points and says brightness now looks better. Keep
all light/material values. Read-only receipt confirms the brighter FX/material
in Archer's build 8 (see art/crown_alarm/intensity_review/brightness_build8.json).
_tod_crown_alarm::init now chooses one server RandomFloat(360) per rotor, offsets
only yaw, and logs phase_degrees. Same common activation, 1.5-second rotation,
fixed housings and inverted pendant. Duplicate init/start never reroll phases.
Actual initialization/lifecycle tests and arity/7816 API-site gates pass.
Updated Blender MCP comparison/motion at docs/crown_alarm/review.html. Phases
not built/synced by this session; request READY in the existing BUILD_HANDOFF.md
for Archer clearance. No game launch. Prior intensity-pass unbuilt notes are
historical; this new random-angle change remains pending the next build.

### 2026-09-26 high crown alarm lamps (Blender agent; source ready, unbuilt)

User requests 4x intensity specifically on the distant crown lamps. The 16
points and apex now select an on-model skin with emission 144 instead of 36;
13 hall fixtures retain the accepted material and spotlight unchanged. Same
geometry, red hue, random starting angles, trigger/seal and 1.5-second rotation.
Tests cover 17 high / 13 hall selections, shutdown and duplicate initialization.
Matched Blender MCP distance renders: docs/crown_alarm/review.html. These are
previews, not native verification. New model/material are required by compiled
and post-build gates. Handoff READY in docs/crown_alarm/BUILD_HANDOFF.md; no
build/sync or game launch. The teleporter screenshot has now arrived; its pink
surface breakup is under investigation, so the earlier screenshot request is closed.

### 2026-09-26 teleporter screenshot correction (Blender agent; SOURCE READY)

The 16:05 native screenshot shows pink breakup across the metal deck. Current
exported binary/UV/atlas renders clean through Blender MCP; the archived log has
one model per transit-pad origin. Read-only private DB confirms inherited
waterRoughness=0.1 on ready/off materials. Fullspec binds it to emissive layerDepth;
the intended atlas preview has no parallax. Likely source of the sampling mismatch,
not a user-verified diagnosis. Explicit depth=0 and gloss range 0..6 now replace
the default depth/0..8 finish in both body materials. Textures, all seven body
LODs, recharge mesh, master, scripts and timing are unchanged. Native source,
state and pixel-mask checks pass. Old build 8 fails the new deployment gate.
Review/evidence: art/teleporter/surface_repair/review.html. Existing profile and
installers preserve the fix; verify_native requires explicit zero depth.
No build/sync or game launch. Added to docs/crown_alarm/BUILD_HANDOFF.md with
the pending FULL color/wires build and random/high-brightness alarms. Archer
clearance still required. Afterward run record_surface_build.py as well as the
existing color and alarm deployment audits. Native appearance awaits the user.
