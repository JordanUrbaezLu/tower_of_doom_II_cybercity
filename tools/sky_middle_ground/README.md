# Approved cyber middle ground

The user approved [this concept](../../art/sky3d/middle_ground_review/concept.png).
The engineered sign, smaller mechanical crest and broader cyber architecture
supersede the gothic v9 gate. Keep the reduced layout, station and celestial space.

Use the dedicated upstream Blender MCP studio on port 9896. The wrapper accepts
only scripts in this folder. It records the actual MCP response. The Python
environment is read-only: always use `-B` and `PYTHONDONTWRITEBYTECODE=1`.

1. Run `check_architecture.py` for lot bounds, elevated UV/geometry parity and
   global RNG independence. Run `mcp_call.py author.py` to author the scene.
2. Run `audit_composition.py`, then MCP `skyline.py` and `clearance.py`. All
   14 retained planet/ring/moon groups must clear the solid skyline by 3 degrees.
3. Run `render.ps1 -Width 4096 -Samples 96`, then
   `finish.ps1 -Width 4096 -Review preview4096`. Inspect the title, city,
   station, upper sky and panorama at the same bracket as earlier versions.
4. Run MCP `finalize_master.py` while the editable master is still open. Then
   `render.ps1 -Width 8192 -Samples 160` and
   `finish.ps1 -Width 8192 -Review final`. Keep the full projected view set.
5. Review the result, run `install.py`, update the measured `SKY_SCORE` in
   `tools/art_cohesion/verify_tower_design.js`, and run MCP `preview.py`.
   The lightweight preview uses Rendered mode and the installed finished HDR.
6. Capture `verify_build.py --snapshot --title-report
   tmp/sky_middle_ground/raw_8192.title.json --title-version cyber_hero_title_1`
   with extra `--receipt` arguments for composition, clearance and preview proof.
7. Run the guarded `tools/build_map.ps1` FULL build, serialized and only when
   BlackOps3 is absent. Close heavy authoring/render processes before the bake.
   Never launch the game. Run `verify_build.py --build-log
   tmp/sky_middle_ground/full.log` after BUILD OK.

`preview_candidate.py` replaces the studio scene with the candidate panorama;
use it only after saving/finalizing the master. The finalizer rejects a preview
scene. Source, artwork, master, paired render/AOV, finish and deployed files are
hash-bound. A changed source requires reauthoring; never patch a receipt to hide
it. Earlier v8/v9 evidence and the approved concept review are historical inputs.

Blender views approximate the display bracket. BO3 bloom, exposure and runtime
performance remain the user's playtest. The case-safe asteroid direction/distance
fix must remain in the compiled fleet script.

To reopen the installed preview, run `open_preview.ps1`. Blender may reset saved
viewports to Solid during file loading; `activate_preview.py` restores Rendered,
Scene World and Scene Lights, verifies the installed HDR against `preview.json`,
and records `preview_activation.json` without resaving the blend. These display
helpers were added after the native build snapshot and do not change built art.
