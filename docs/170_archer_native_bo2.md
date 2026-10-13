# Native BO2 Retriever integration

User baseline (2026-09-25): Hell's Retriever should behave like the original
BO2 version before making gameplay iterations. It occupies Archer's lethal
slot as requested; the custom grapple occupies tactical. No fall damage.

## Source and implementation

`_tod_retriever.gsc` replaces the old manual 900-unit, three-hit axe. Its
reference is the retained Alcatraz `_zm_weap_tomahawk.gsc`, alongside the
original `bouncing_tomahawk_zm` weapon definition. BO3 owns grenade input,
pullback, release, the initial projectile, collision and first-person rendering.

| Behavior | BO2 baseline used |
| --- | --- |
| Initial projectile | 920 units/sec; original .048-second release delay and .32-second fire time |
| Native flight handover | Collision/death or .5 seconds, then a script mover |
| Charge feedback | Pulses at one and two seconds |
| Damage multiplier | 1 / 1.5 / 2; original strict comparisons at exactly 1000 and 2000 ms retained |
| Initial search | Zombies and power-ups within 200 units; power-ups take priority |
| Initial attack | Closest live marked zombie within 70 units |
| Chain | Original reversed 300-unit candidate order; first four entries; only targets marked by the initial search are eligible |
| Attack travel | .3 seconds per attack; .2 seconds between chain entries |
| Return | Retarget owner's eye every .1 seconds using a .25-second move; original 64-unit horizontal catch threshold |
| Return attacks | Original nearby 100-unit search and five-check budget |
| Damage | 1000 times charge; original round 10-12 / 13-14 instant-kill counter rules |
| Points | Original extra 10 points per scripted hit |
| Recharge | Five seconds after catch; max-ammo cannot bypass an active throw/cooldown |

Per-throw hit tracking replaces BO2's shared zombie flags to keep co-op players
independent. Cleanup handles death, downing, class changes, disconnect and
respawn. Map menus pause the shared cooldown/state clock. The grapple keeps
ordinary player collision and its existing 128-3000-unit aimed-surface pull.

## First-person and material assets

The original 2501-triangle Retriever view model and 7240-triangle Alcatraz
Arlington hand model retain their geometry, UVs, normals and weights. The native
offhand uses the original hand skeleton and `tag_knife_attach`, avoiding an
approximate skeleton retarget. Four recovered clips are converted at 30 fps:
hold (6 frames), throw (21), acquisition flourish (48), and flourish idle (11).
The original flourish sound notetrack is remapped to its recovered audio alias.
BO2 has no separate catch-hand animation; its catch uses sound and recharge.

`read_t6_anim.py` decodes OAT's v19 keys. Blender evaluates absolute local hand
tracks and bind-relative `j_gun` descendants, then exports native BO3 animation
binaries. The relative weapon-track distinction follows
[Greyhound's translator](https://github.com/Scobalula/Greyhound/blob/master/src/WraithXCOD/WraithXCOD/CoDXAnimTranslator.cpp).
Original rig positions are inches. Render previews show hold/throw/flourish.

The grapple's separate native inventory item raises, holds and lowers the arm
and wrist housing. Its 2200-triangle model combines the recovered Apex component
with a housing authored through Blender MCP. It restores the exact previous
weapon and includes bounded failure/cleanup paths. This is custom grapple art;
BO2 has no Pathfinder grapple.

The blade's original reveal, ember and heat maps now drive a native BO3 emissive
flipbook: 64 frames, 512x512 pixels per frame, 4096x4096 atlas, original UV scroll
directions and 100-second common period, brightness 10 and flicker .85-1.1.
This is a renderer translation of BO2's custom shader, not pixel-identical T6
shader execution. The atlas adds animation frames, not invented source detail.
Charge and charged-trail effects are included alongside the trail and impact.

Master: `art/archer_assets/archer_equipment.blend`. Previews include
`bo2_throw.png`, `bo2_flourish.png`, `retriever_ember_flourish.png` and
`grapple_first_person.png`. Blender renders do not prove native visibility.

## Runtime blocker found and fixed

The user's archived log in
`tmp/archer_assets/playtest_logs/20260925_011939_553_d686b713/console_mp.log`
shows the earlier build failed to load because `LoadFX` is not a BO3 GSC
builtin. Both Archer modules now use `#precache("fx", ...)` and native FX path
strings. `test_retriever_native.js` rejects a regression. A successful compile
alone did not establish that the previous map could boot.

Native conversion also exposed three asset compatibility issues, now corrected:
the flourish binary uses the official BO3 exporter with an executable frame-0
sound action; the recovered charge-ring texture uses BO3's supported
`effect_lit_emissive_add` with a 1x1 atlas; and the grapple housing uses
`$white_diffuse` / `$white_specular`, not the UI-only `$white` image.
The deployment audit rejects Archer-specific linker warnings as well as missing
ledger entries, including material failures that lack an `ERROR:` prefix.

## Verification and diagnostics

- `test_archer_equipment.js`: 54 grapple, input, fall-immunity and lifecycle checks.
- `test_archer_art.js`: executable client callback and idempotent cleanup checks.
- `test_tod_native_api.js`: all 6,281 engine call sites across all 96 map
  scripts have same-VM, same-argument-count evidence in installed reference
  scripts, official SDK documentation or retained stock DLC references.
  Includes local inserted headers and valid optional arguments. Rejects server
  `LoadFX` / `StopFXOnTag` and client `PlaySoundAtPosition`. This is a build
  gate, not a substitute for native execution.
- `lint_tod_arity.js`: all 96 scripts; case-insensitive namespace resolution,
  multiple namespaces in one file, missing namespaces and excess arguments.
- `test_script_startup_gates.js`: five in-memory negative controls verify that
  the actual linters reject both reported calls, the invalid third-person
  argument count, an unknown namespace and an excess-argument script call.
  Does not alter shipping files or overwrite the passing evidence report.
- `test_retriever_native.js`: executes shipping charge/damage/state-machine code,
  including chain ordering, travel timing, score, power-up catch, cooldown and
  native projectile handover.
- `verify_retriever.py`: original source hashes, world geometry and texture sizes.
- `verify_native.py`: 14 original weapon fields, view geometry, animation frames,
  rate, sound notes, original hand textures and stable asset names.
- `verify_archer_deployment.py`: compiled assets/models/sounds and hashes of all
  deployed inputs, including native first-person animation binaries.

`[TOD_RETRIEVER]` logs EQUIP, PULLBACK, CHARGE, CHARGE_CANCEL, THROW, IMPACT, HIT,
RETURN and END with owner, charge, damage, round and target context.
`[TOD_ARCHER]` adds VIEW_START, VIEW_SELECTED, VIEW_FAIL, VIEW_END and AXE_READY
to the existing grapple/fall diagnostics. Client cable diagnostics remain
`[TOD_ARCHER_C]`. Logging is automatic under dev mode and change/event based.
`capture_ai_logs.ps1` includes both Archer modules and the Retriever module in
its source-hash manifest.

Build/deployment evidence is `docs/archer_equipment_evidence/build.json`.
Original/native source checks are `retriever_source.json` and
`native_sources.json`. The user performs the native playtest; do not launch
BO3 without an explicit agent-run-match request.

## First implementation build evidence - superseded by the 03:07 runtime failure

Full native-asset/geometry build passed at 01:49:25 Eastern
(`tmp/balcony_build/build.log`). The subsequent script rebuild passed at
01:54:18, including the input-restoration fix that missed the full
build's initial sync. Final fastfile: 206,962,368 bytes; SHA256
`ed4d67f60bff5d155d014d7226e7e748bba2a7e82a9b59424b3d133fbcb6d15e`.

All 261 audited map/art inputs match deployment and predate the final
fastfile. All seven clips, six compiled models/eight LODs, twelve sound
aliases and their native dependencies are present, with no Archer linker
warnings. Loaded/streamed banks are 109,442,176 / 209,338,496 bytes. The existing
eight unrelated waived linker diagnostics remain unchanged.

`full_geometry.json` proves the map, BSP, navigation and LED hashes are unchanged
from the full build. The peer balcony and Veil changes are included.
`roster_build.json` records 350 matching inputs, 240 expected weapon/model assets
and 174 local sound aliases. Dev and god mode remain enabled. The inherited
Peacekeeper common-bank dry-fire caveat remains recorded in that roster report.

Those source, conversion and linker checks passed, but did not validate all
runtime APIs: the user's 03:07 playtest failed before the map could load.
No successful native test of that build should be inferred from these checks.

## September 25 load failure: unsupported server FX cleanup

The user's screenshot and archived console agree: `_tod_retriever.gsc:347`
called unresolved external `StopFXOnTag` with three arguments. Raw evidence:
`tmp/archer_assets/playtest_logs/20260925_030743_953_56465bf3/console_mp.log`,
lines 3557-3563. The game was in its fatal-error dialog, not an active match.

Both unsupported cleanup calls were removed. Attached trails are owned by the
axe entity; cleanup deletes that host, following stock BO3
`_zm_ai_raps.gsc` (`cleanup_meteor_fx`, lines 714-726, and the meteor deletion
at lines 671-681). Spin audio still stops before its separate emitter is deleted.
Existing per-throw diagnostics and idempotent cleanup remain intact.

The old behavioral test mocked `StopFXOnTag`, so it could not establish that
BO3 actually exposes the API. That stub and the misleading cleanup expectation
were removed. The new engine-API gate failed on the broken shipping code before
the fix and passes afterward. Evidence is `native_api.json`; the original
negative result is `tmp/archer_assets/native_api_before_fix.log`.
This check verifies observed stock usage by script VM and argument count;
native startup and gameplay still require the user's next playtest.

## September 25 second load failure and map-wide review

The next user launch passed server initialization: `[TOD_ARCHER] INIT`,
`[TOD_ROSTER] REGISTER`, partner and shop initialization appear in
`tmp/archer_assets/playtest_logs/20260925_031607_731_f92a6d9f/console_mp.log`.
Client loading then failed in `_tod_boss_fx.csc` on `37CBCF1A` with three
arguments. The T7 name hash of `playsoundatposition` is exactly `0x37CBCF1A`.
The official SDK documents that function for the server VM only; both client
calls now use `self PlaySound(localClientNum, alias)`, preserving sound at the
boss/partner actor. Clientfield layout, pulse/initial-snapshot guards and FX
placement are unchanged. `SetDrawName("")` remains valid: its second argument
is explicitly optional in the SDK.

At the user's request the review was expanded from Archer/boss to the entire
script tree. It found a third-person toggle passing unsupported camera range
and height arguments. `_zm_aetherium_hud.gsc` now uses the documented one-flag
form and native camera settings. The Panzer's `HideViewLegs()`/`ShowViewLegs()`
are valid stock DLC calls absent from the older installed SDK; exact source,
commit, lines and hash are retained in `dlc_native_api.json` from the
[native claw script](https://github.com/shiversoftdev/t7-source/blob/07cbfcd113fb5031dc717296f73b371478d4eb77/scripts/zm/_zm_ai_mechz_claw.csc).
These were retained, not replaced based on a documentation gap.

The namespace lint previously skipped unknown namespaces, compared namespace
case literally and indexed only the first namespace in each file. It now
handles the stock case/multiple-namespace patterns and rejects unresolved
namespaces across all 96 scripts, including shared AI sources. Both linters
pass, with the five negative controls proving they reject representative
startup failures. Their evidence is static: dynamic state, native asset
appearance, sound and full gameplay still require the user's playtest.

The first cleanup rebuild (`tmp/archer_assets/stopfx_load_fix_build.log`)
linked at 03:13:56, but its final guard FAILED because BO3 launched during
post-build checks. It is not a successful guarded build. The user's ensuing
run supplied the client failure above. A fresh guarded rebuild with all
three corrections is recorded in `tmp/archer_assets/startup_review_build.log`;
final deployment evidence is recorded below only after completion.

## Completed startup-fix build

The guarded script rebuild exited 0 and reported BUILD OK. Fastfile:
`2026-09-25T03:26:57.926904` Eastern, 206,962,048 bytes; SHA256
`a161b014b55d5f767ad39e2021bf5661fb8cb0f1b1bdc77d4d78208f4c88157d`. Transcript: `tmp/archer_assets/startup_review_build.log`.
All 96 reviewed scripts match deployment. The Archer audit passed all 261
inputs; roster audit passed 350 inputs, 240 weapon/model assets and 174 local
sound aliases. Seven Archer clips, six models/eight LODs and twelve aliases
remain present. Loaded/streamed banks: 109,442,176 / 209,338,496 bytes.
Dev/god remain ON. No source sync followed the fastfile. Geometry and lighting
hashes match the 02:57 sky-v4 full build; the eight previously waived linker
diagnostics are unchanged. The inherited generic common-bank dry-fire aliases
remain outside the roster audit's proof.

`startup_review.json` records the reviewed script hashes, callback review,
five negative controls and successful guarded build. All 400 script callback
references resolved; two localized-string macros and two supported native
PlaySound pointers were classified separately. No agent launch occurred;
successful native boot and gameplay remain pending the user's retest.

## Follow-up 2026-09-25 (the sky session): the ammo-counter icon

The user's first run that reached the Archer's arm (11:25, the 11:20 blackout build) fataled with
`Com_ERROR: Primary Grenade Ammo Counter Icon Not Found for: tod_archer_retriever` (console_mp.log line 3842,
archived under tmp/elite_tracking/runs/20260925_112858_812_2ed4d474). The engine requires an ammo-counter
MATERIAL on any offhand in the lethal slot; the recovered BO2 block had none. `install_native_weapons.py` now
emits `ammoCounterIcon "t7_icon_weapon_special_knife_pu"` and `ammoCounterClip "None"` (the stock knife icon:
proven in that role by 100+ weapon blocks in the tools root) and the GDT was regenerated - two lines added.
Follow-up for the Archer pass: a 2d material over `i_tod_archer_axe_hud` so the counter shows the tomahawk.
