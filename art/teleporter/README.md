# Cybercity teleporter

September 26, 22:40: the user accepts the repaired metal surface. New status
colors are GREEN ready, animated YELLOW pending, no device light without power.
The old pink-ready palette is superseded. [Current review](states_review.html)
and [source/build notes](status_colors/README.md). BUILT in Archer's full build
16c; the deployed palette/FX/material/script/LOD audit passed at 23:00 Eastern.
The new colors await the user's game test. No game launched by this session.

Archived studio session (September 24, 22:24):
[complete session](checkpoints/20260924_222406_saved_session.blend).
Saved through Blender MCP, reopened successfully with 480 objects, then
closed at the user's request. The exported `teleporter_cyber.blend` is preserved.

The September 20 reference's lower image guides the layered alloy deck,
recessed rings, copper induction cassettes and central emitter.
This is a modeled prop, not a screenshot mapped onto a disc.

September 26 corrects the three availability states through live Blender MCP
and native scripts: **off** has dark glass and zero emission;
**ready** has green neon strips; **pending** has a yellow quarter-circle
chase around the rim, one revolution every three seconds. The chase has a
bright head and fading tail. Power loss overrides recharge and removes all
device lights. Powered destination locks and upgrade pauses also show the
yellow pending chase. Explicit shutdown stays dark.

Open `states_review.html` for the six-second animation and three stills.
These are Blender previews; native BO3 appearance remains for the user.
The Blender studio stays on port 9879. Scene `teleporter_preview_auto=0`
enables manual `teleporter_state`: 0 off, 1 ready, 2 pending.

- `teleporter_cyber.blend`: editable Blender MCP master, 446 named parts.
  The original nine-piece native assembly is preserved in a hidden collection;
  four clipped lower-casting pieces remain in the enhanced model.
- `teleporter_native.blend`: reduced mesh with the actual five baked maps.
- `hero.png`: master render; `native_low.png`: baked mesh at a lower angle.
  These are Blender previews, not BO3 screenshots. BO3 lighting/bloom remains
  for the user's playtest.
- `original_sources.json`: original native paths, hashes, materials and bounds.
- `engine_kit/`: seven LODs, source/install manifests and validation reports.
- `checkpoints/before_power_states.blend`: preserved pre-state master.
- `state_off.png`, `state_ready.png`, `state_recharging.png`,
  `states_preview.mp4`: current state review; older hero renders show the
  superseded cyan/violet palette.

The model is floor-relative at native scale: X/Y ±77.5, top 9.46 units.
It replaces nine script models with one at all eight transit pads and the
crown ascension pad. Existing triggers, positions, power/door conditions,
0.8-second charge and 60-second recharge remain unchanged. September 22 adds
low ready rings, charge contraction and release pulses (docs/152). No collision
is introduced, preserving the original walk-through and navigation behavior.

Authoring used the upstream Blender MCP addon via a real MCP ClientSession on
isolated port 9879. The teleporter scripts are in `tools/teleporter/`:

1. `python inspect_source.py` records the original installed assets.
2. Start Blender with `--python mcp_bootstrap.py`.
3. Run `mcp_call.py 01_author.py` with the installed MCP Python environment.
4. Background Blender runs `export_native.py` (2048-square maps, DirectX normals,
   color, specular, gloss and emission; seven connected-part distance LODs).
5. `python install_native.py`, then `python verify_native.py`.
6. Take `verify_deployment.py --snapshot`, run the repository's full build,
   and run `verify_deployment.py`. Build gates check native triangle coverage.

The installed MCP environment on this machine is
`../tower_of_doom_II_hellbound/tmp/gold_sword_env/Scripts/python.exe`.
Its upstream addon is in that project's `tmp/blender_mcp_vendor/addon.py`.
All native model/texture inputs live in this repository. Those neighboring
paths are needed only to reproduce MCP authoring, not to build the game.

Dev mode emits `[TOD_TELEPORT_MODEL]` once per pad creation, recording model,
origin, yaw and success or allocation failure. Capture a user's console with
`tools/capture_ai_logs.ps1`. No agent-run game was requested or performed.

Full build passed September 20 at 11:52 Eastern. All seven compiled LOD counts
match exactly; model/material/five maps are packed, and all 161 snapshotted
inputs match the deployed tree. Build evidence: `tmp/teleporter_build/`.
Native appearance and diagnostic output await the user's playtest.

## Reproducing the states

After the original bake, run `04_power_states.py` through `mcp_call.py` in
the open studio. Background Blender runs `05_export_states.py`, then normal
Python runs `install_states.py`. Background Blender's `06_render_states.py`
creates the state previews. `check_state_images.py` (Pillow) proves that
the emission mask and peak radiance are preserved and that darkening the
glass changes no non-glowing metal texels. `verify_native.py` includes
state/source checks and compiled coverage; `test_states.js` executes the
actual state functions with mocks. The combined September 24 deployment
verifier is `tools/partner_shop/verify_deployment.py`.

The body retains all seven existing LODs. The ready/off models share that
geometry with separate materials. A cooling pad owns one extra 1,152-triangle
mesh, three emissive bands, no collision and no new dynamic lights. Model
state and rotation replicate from the server. The sixty-second cooldown and
0.8-second travel charge are unchanged. The deferred ascension pad uses the
same availability logic. The separate, always-usable jump pad shares the green
ready field and retains its original availability rules.

`[TOD_TELEPORT_STATE]` records state edges, reasons and chase allocation
failures. Temporary `TOD_TP_STATE_LOG 1` captures the first normal-match
playtest; turn it off after acceptance, leaving dev-mode logging. The capture
tool now includes the teleporter script hash. Native testing remains pending.

The combined shop/teleporter full build passed September 24 at 13:58
Eastern. All state models/materials and the pink map are packed, native
triangle counts match exactly, and all 348 snapshotted inputs match the
deployed files. Evidence: `tmp/partner_shop_build/full_build_9.log`,
`deployment.json`, `final_build_record.json`. The Blender preview is open
and cycling through the states. BUILT AND STOPPED; no game launch.
