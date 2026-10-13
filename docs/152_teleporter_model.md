# Teleporter model enhancement — September 20, 2026

## September 26: native surface screenshot follow-up

The user's native screenshot reveals pink breakup across metal plates. The
exported binary renders clean atlas strips through Blender MCP. Native DB
inspection instead found inherited emissive depth 0.1, absent from the intended
surface-aligned Blender material. Both ready/off body materials now explicitly
use depth 0 and a softer gloss range 0..6. This is a likely correction, not yet
a native-verified fix. All textures, geometry, states and timing are retained.

Source/state/image checks pass. Review and evidence:
[surface correction](../art/teleporter/surface_repair/review.html).
Awaiting Archer's cleared build; run tools/teleporter/record_surface_build.py
after it. No game launch. The user's next test must confirm the pink stays on
the recessed strips as the camera moves.

## September 24: off, pink ready and yellow recharge

The existing 446-part Blender MCP model now previews three availability
states in `art/teleporter/states_review.html`. Off has dark physical light
strips and no emission. Ready uses pink neon. During the existing 60-second
cooldown, an eighteen-segment yellow arc circles the rim every three seconds,
with a bright head and dimmer tail. Power off or a locked destination keeps
the pad dark; an upgrade pause also darkens an otherwise-ready pad.
All original body geometry and travel
timing remain unchanged. Older cyan/violet renders below are historical.

Native `tod_teleporter` and `tod_teleporter_off` share seven body LOD files;
the material twin controls emission. The original glow mask and peak values
are preserved in a pink map, and only emissive glass pixels are darkened in
the diffuse map. A cooling pad owns one 1,152-triangle `tod_tp_recharge`
mesh with three emissive bands and server rotation. No new dynamic lights,
particles or collision. Existing ready FX disappears when unavailable.
Eight transit pads use this logic; the deferred ascension pad has the same
power/availability hook. The independent, always-usable jump pad stays pink.

`test_states.js` executes the real GSC state bodies with mocks: power and
destination gates, recharge/expiry, interrupted power, upgrade pause,
allocation failure/retry and chase cleanup. `verify_native.py` now also
checks shared LODs, material mappings, source hashes and compiled state-model
coverage. `check_state_images.py` proves the texture edit's scope across
4,194,304 pixels. The Blender state render verifies emission/visibility.

`[TOD_TELEPORT_STATE]` automatically records state edges and failures in the
first normal-match test (`TOD_TP_STATE_LOG 1`; zero after acceptance).
`tools/capture_ai_logs.ps1` archives the console and script provenance.
The combined shop/teleporter build evidence lives in
`tmp/partner_shop_build/`. Runtime appearance, timing and diagnostics await
the user's playtest. No game launch is authorized by this art/state task.

Full build and deployment checks passed September 24 at 13:58 Eastern.
FF 211,206,016 bytes (13:56:30); LED 100,163,686 bytes, freshly baked.
Ready/off body LODs and the 1,152-triangle recharge ring match compiled
geometry exactly; both material variants, all three chase materials and
the pink emission image are packed. The combined 348-file snapshot matches
deployment with no missing assets or inputs newer than the FF. Evidence:
`tmp/partner_shop_build/full_build_9.log`, `deployment.json`,
`final_build_record.json` and copied asset ledgers. The MCP preview is running
without resaving the hashed master. BUILT AND STOPPED; no game launch.

## Original model pass

User requested improving the current teleporter through Blender MCP toward
the lower supplied reference. `art/teleporter/README.md` records the editable
master, preserved original, reproducible scripts and previews.

The upper pad now has beveled segmented armor, copper cooling cassettes,
fasteners, ceramic reactor panels, service markings, recessed cyan/violet
conductors and a central iris. The existing lower casting is retained.
The original full assembly stays in a hidden Blender reference collection.

The native export uses one material and five shared 2048-square maps, with
49,324 / 30,727 / 16,546 / 12,903 / 10,566 / 9,008 / 5,000 triangles.
Distant simplification is constrained to the authored LOD0 bounds. No shader
requires runtime transparency. Explicit diffuse, normal, gloss, specular and
emission channels use the project's established fullspec material technique.

`spawn_der_teleporter` remains the public shared function, so the spire caller
uses the same appearance. Nine original fragments per pad become one model.
The eight transit pads and crown ascension pad keep their original origins,
yaws, triggers, travel conditions, charge/cooldown, beam and teleport effects.
The new model has no bullet or movement collision. Dev/god flags stay as found.

Source checks validate geometry tables, root weights, finite UVs/normals,
footprint, seven LODs, file hashes and shared wiring. The full build also
checks every LOD's compiled triangle count. Exact deployed-input and packed
asset evidence is written to `tmp/teleporter_build/`.

The Blender previews demonstrate modeled detail and baked texture retention.
They do not establish native BO3 gloss/glow appearance. The user tests;
the agent builds and stops. `[TOD_TELEPORT_MODEL]` automatically records
dev-mode initialization and allocation failures, including origin/yaw/model.
The new diagnostic's runtime output is pending the user's dev-mode playtest.

Build status: FULL BUILD passed September 20 at 11:52 Eastern (exit 0), with
fresh BSP/navigation and a 45,149,178-byte LED. FF written 11:45:41 is
179,327,872 bytes; sound banks are 207,523,840 and 57,466,112 bytes. All seven
compiled triangle counts match exactly; model, material and all five images
appear in the packed asset ledger. All 161 snapshotted inputs match the source
and deployed trees, with no deployed input newer than the FF.

The full build also picked up the concurrently completed evil sky: deployed
EXR hash equals source and a fresh 21,681,431-byte
`i_skybox_tod_cybercity_7SQVLRM3ZWWD4VZ6TPCUEZ7N7F.iwi` was converted.
Evidence is in `tmp/teleporter_build/` (full log, snapshots, asset ledgers,
deployment report, world input hashes, LED and sky conversion records).
The earlier successful cached-geometry relink is archived under `shared_relink/`.
No game launch or native visual verification.

## September 22: isolated Tower II integration and FX

The deployed legacy folder had been replaced by Map One's old assembly.
Tower II now owns `zm_tod2_cybercity` in its private tools workspace (docs/154).
The same enhanced native model serves all nine placements, with unchanged
footprint, non-solid behavior, travel rules, 0.8-second charge and 60-second recharge.

Three map-owned FX sources are authored by `tools/teleporter/generate_fx.py`:
low cyan/violet ready rings and rising ions; a contracting charge field;
and expanding departure/arrival rings with a brief floor light. The deck
remains visible. Stock electrical charge, flash and arrival layers remain.
New charge/release layers share the existing host and cleanup, so they add no
script entities. The two server-frame replication delay remains intact.

`test_teleporter_fx.js` executes the GSC host body with a mocked scheduler:
replication delay, a shared host for both layers, timed deletion, failed spawn,
missing assets/overlay and host loss all pass. The generator's `--check` and
lifetime test run automatically in the build. `[TOD_TELEPORT_FX] rev=2` records
pad-state edges, emitted layers, failures and completion with a lifetime ID;
logs use the existing dev-mode switch. Runtime appearance and log output await
the user's playtest. Evidence: `tmp/teleporter_fx_20260922/`.

## September 23 build status: packaging pending

Private geometry/navigation passed and Radiant wrote a fresh 45,149,178-byte
LED at 14:58:48 Eastern. The linker failed before producing the new fastfile:
`i_generic_lookup` required the missing stock `sw4/textures/tv_lookup.tif`.
The eight-file library is now physically copied into the private workspace;
setup and preflight cover it. FX source/lifecycle checks and private database
ownership checks pass. BO3 then started Map One, so no further build ran.
After the game closes, finish packaging and `verify_deployment.py` before
calling the new isolated map ready to test. No game launch or visual approval.

The model was authored in Blender MCP. These FX use existing native sprite
art; custom Blender FX masters and animation previews have not been made.
The shared art workflow is recorded in `docs/155_fx_art_workflow.md`.
