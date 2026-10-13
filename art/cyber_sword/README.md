# Cyber Sword — authored, integration staged

The Gold Battle Sword is now a dark cyber weapon in an editable Blender MCP
master. Titanium cutting planes, cyan edge rails and branching circuits,
violet charge cells, cobalt hardware and a blue reactor replace the gold finish
and raised lettering. Original grip, silhouette, eight bones and animation
clips are retained. The original Downloads master is unchanged.

Open `cyber_sword.blend`: frame 1 is charging, frame 60 is ready. The scene's
`cyber_charge` property controls the materials. `native_preview.blend` instead
uses the actual exported geometry and five 4096-square game maps. That preview
approximates fullspec shading; it does not reproduce BO3's probes or exposure.

## Runtime behavior prepared

The class kit supplies its existing HUD result to `_tod_cyber_sword::update`.
Tier 3 + zero kills remaining + not casting = ready. Existing dev unlimited
behavior is respected. Presentation never grants charge or changes damage.
The view material rises to full glow in 300 ms, immediately darkens when spent,
and reattaches on a weapon/form switch. The slam uses its own illuminated skin;
the bash retains current readiness. Both proxies preserve all donor animation,
sound and timing fields. No particles, dynamic lights or weapon swaps are added
by the readiness effect. Dev logs are edge-only `[TOD_CYBER_SWORD]` messages.

Readiness glow is first-person, via the established `scriptVector2.y` channel.
Third-person ordinary/bashed swords use the colored, unlit inlays; the third-person
slam uses the lit skin. Remote-player readiness replication is not implemented.
Native material brightness, grip clearance during swings/slam and split-screen
behavior still require the user's game test after a cleared build.

## Assets and checks

- Seven explicit meshes: 48,777 / 26,990 / 14,617 / 9,098 / 5,229 / 3,859 / 2,755 triangles.
- Five maps: diffuse, DirectX normal, fullspec reflection, gloss and emission.
- Only about 3% of the atlas carries emission; depth is explicitly zero.
- Three materials; four model definitions share the same seven mesh files.
- New slam/bash weapons preserve their donor fields except name and models.
- `source_data/tod_cyber_sword.gdt` and `zone_source/tod_cyber_sword.zpkg`.
- `tools/cyber_sword/verify_native.py`: original source/bones, files, UVs, normals,
  cool glow mask, geometry counts and unchanged move fields.
- `tools/cyber_sword/test_state.js`: executes the actual GSC/CSC bodies with engine
  boundaries mocked, covering readiness, busy/tier/dev/class/death and switching.

Native export review caught invalid weighted normals on thin cutting planes.
The baker now rebuilds normals after reduction and keeps those planes flat;
export also rejects normals pointing into their own triangle. Review the
exported atlas/mesh, not just the high-resolution authoring master.
The binary preview must also split native corners instead of welding solely
by position: Blender's thin-edge normal fans otherwise create false dark
triangles. Its normal reconstruction error is now checked before rendering.

## Archer integration — pending

The repository's lead rule reserves shared edits and all builds for Archer.
No shared working file, deployed input, database or game has been changed by
this sword pass. The concrete four-file patch and matching staged copies are
in `integration/`; its baseline hashes make concurrent changes visible.

1. Review `integration/shared_integration.patch`. Regenerate it with
   `python -B tools/cyber_sword/stage_integration.py` if shared files have changed.
2. After lead clearance: `git apply --check --ignore-space-change
   art/cyber_sword/integration/shared_integration.patch`, then apply with the
   same whitespace option (the existing Windows files have CRLF endings).
3. Lead regenerates `gen_tod_twins.js` once. The stem stays `cc_gold_sword`;
   all base/PaP variants bind to the new models. The package supplies both proxies.
   Existing `model_export/tod_warrior` and source_data sync already cover the art.
4. Run the ordinary repository gates plus `verify_native.py --integrated`,
   `node tools/cyber_sword/test_state.js`, and the cleared guarded build.
5. `python -B tools/cyber_sword/record_build.py --build-log <log>` verifies actual
   packed assets, native material settings, compiled LOD coverage and matching
   deployed inputs. It must fail against a build that still contains the gold art.
6. User plays. Charge, cast, switch away/back, PaP, die/respawn and change class;
   archive their console with `tools/capture_ai_logs.ps1`.

Reproduction: MCP `01_inspect.py`, `03_author.py`, `05_prepare_native.py`; then
background Blender `06_bake_native.py`, `07_reduce_lods.py`; Python
`install_native.py`, `verify_native.py`; background Blender `08_native_preview.py`
and `09_motion_preview.py`. `12_rebake_normal.py` / `11_reexport_normals.py` are the
normal-only repair route, followed by the same LOD/install/verification steps.
