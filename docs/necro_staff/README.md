**Latest correction: original staff pose and outgoing white souls BUILT and deployment verified at 23:07 Eastern. Ready for user playtest.** See [playtest correction](POSE_AND_SOULS.md) and `tmp/necro_staff_build/status.json`. Older build receipts below predate this correction.

# Necromancer staff tiers

User reference: Screenshot 2026-09-27 145453.png. Tier 1 retains Nan Sapwe.
Tier 2: a carved human skull mounted on an aged dark metal staff, no spikes;
simpler collar and shaft ornament. Tier 3: the reference silhouette: ivory skull,
circular pierced metal crown, six lateral angular spikes, long spear-shaped
upper finial with two smaller flanking shards, forked collar and engraved shaft.
Both are new assembled models. Bone pores, cracks, engraved metal, bevel wear,
separate teeth, deep sockets and material response must remain readable in
first person. No flat-color placeholder surface or preview-only geometry.

Use actual Blender MCP; keep editable source, exported native meshes/UV/maps,
first-person motion review and source receipts. Use Map One ice-staff rigs and
approved animations as read-only references. All outputs belong to Tower II.
Skull beam/torch effect tags travel with the head. Staff channel-in/hold/out
and summon pose must retain both hand grips; never run handheld-skull arm poses
unchanged on a staff. Preserve current meter, tier damage, summons and pulse.

Validation: no missing images, correct bone/animation bindings, continuous
hand grips and cast loops, expected tier/PaP variants, clean FX cleanup,
compiled asset coverage and exact deployment. Build through guarded scripts;
never launch the game. Native quality requires the user's playtest.

## Implementation

New model families `tod_necro_staff2` and `tod_necro_staff3` have separate view/world meshes, three distance LODs, an exclusive baked 2K skull UV/color/normal atlas and separate authored 2K chased-iron/forged-blade maps. Editable Blender source and native-pose review are in `art/necro_staff`; all authorship/export calls have actual Blender MCP receipts under `tmp/necro_staff_mcp`.

The six Necromancer tier/PaP forms now progress from the original skull to Soul Staff and Crown of the Damned. Both staffs inherit the player's viewhands and approved ice-staff handling, including sway, idle, recoil presentation, depth of field and the four slide clips. All 34 animation assets are registered; no handheld-skull movement clips remain. Custom channel-in/hold/out preserves both grip distances and blends stock skull casting cadence into the staff pose. Soul Pulse uses a short non-damaging item animation, with lifecycle cleanup and restoration guarded against weapon switches, death, downing and respawn. Meter, ability damage and the earlier clean white pulse remain on the existing gameplay path.

Diagnostics: `[TOD_NECRO] STAFF_EQUIP`, `STAFF_PULSE_START`, `STAFF_PULSE_POSE`, `STAFF_PULSE_END`, `STAFF_PULSE_FAIL` (the latter four use `[TOD_NECRO_SUMMON]`). Delayed casting FX now carry a mode epoch so an interrupted cast cannot re-enable an old loop.

These are new screenshot-guided assets, not the original reference model or its exact texture set. Blender lighting is approximate. ADS/movement clips retain their original partial-track semantics; the static summon image shows the underlying grip, not a native ADS composite. Native lighting, animation transitions, multiplayer attachment and FX alignment require the user's playtest.

Status: FULL build and exact-source deployment verified; ready for user playtest. See [detail pass 3](DETAIL_3.md) and [iteration 2 corrections](ITERATION_2.md). Only `built` in `tmp/necro_staff_build/status.json` confirms the current receipt. The 17:17 pass was visually rejected; the subsequent 18:27 attempt did not complete its wrapper audit. No agent game launch.


## User playtest focus

Check T1 -> T2 -> T3 and the PaP forms, then hold/release beam, hold summon through conversion, and trigger Soul Pulse. Inspect the crown at idle and while walking/raising the staff, both grips, and whether the white soul effects originate at its head. Try swapping away during pulse and check that no casting loop or temporary weapon remains. The automatic equip/cast/pulse logs identify the held form and cleanup path. Use `tools/capture_ai_logs.ps1` to archive `console_mp.log` after the user plays. No agent-run match is authorized.

Native integration gate: every authored material requires an explicit valid `surfaceType`. The first linker attempt caught a missing value; iron now uses `metal`, bone/soul use `flesh`, and `verify.py` rejects missing types before a build. The failed transcript is preserved under `tmp/necro_staff_build/native_surface_error.log`.

Diffuse integration gate: native diffuse images use `compressed high color` with `sRGB3chAlpha`; normal/gloss/specular maps retain their appropriate linear formats. The image-format failure transcript is archived as `tmp/necro_staff_build/native_image_error.log`.
