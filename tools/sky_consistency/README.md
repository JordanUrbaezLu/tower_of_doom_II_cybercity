# City consistency and readable celestial detail

Carry the approved close buildings' worn cyber materials and architectural kit
through all 1,189 ordinary lots. Preserve the eight preferred hero towers, the
reduced 1,222-building layout, the recognizable station, the approved imposing
title and the measured cinematic/planet clearance. Reduce celestial overglow at
its sources rather than dimming the city or changing native sky exposure.

This pass fixes finishing gain at the reviewed baseline's exact
`0.016525428679573573`. The first candidate's mean-normalized gain rose about
40%, brightening unchanged city/nebula areas and counteracting local dimming.
`finish_profile.json` binds the chosen gain to the preserved baseline stats hash;
`finish.ps1`, the installer and build snapshot all enforce it. `target_score=.64`
remains nominal metadata, while `score_city` and `score` are measured results.
Update the whole-sky `SKY_SCORE` gate from the final measured value. Native SSI,
skyStops and the preview display bracket stay unchanged. Earlier pipelines omit
`--fixed-gain` and retain their existing target-score behavior.

The approved title source remains `art/sky3d/sign/v10_cyber_hero.png`, with exact
title report version `cyber_hero_title_2` (neutral frame highlight compression;
same artwork, alpha, lettering and cinematic placement). Earlier reviews remain
unchanged in `art/sky3d/middle_ground_review/`. Baseline comparison images and the
actual approved lot records are preserved in this pass's `review/before/` folder;
`baseline.json` records their hashes and source paths.

Use the dedicated real upstream Blender MCP studio on port 9896. Only one agent
may own that scene at a time. The wrapper accepts scripts in this folder only.
The sibling Python environment is a read-only tool input: always use `-B` and
`PYTHONDONTWRITEBYTECODE=1`.

From the repository root in PowerShell:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$mcpPython = '..\tower_of_doom_II_hellbound\tmp\gold_sword_env\Scripts\python.exe'

python -B tools/sky_consistency/check_architecture.py
& $mcpPython -B tools/sky_consistency/mcp_call.py tools/sky_consistency/author.py
python -B tools/sky_consistency/audit_composition.py
& $mcpPython -B tools/sky_consistency/mcp_call.py tools/sky_consistency/skyline.py
& $mcpPython -B tools/sky_consistency/mcp_call.py tools/sky_consistency/clearance.py

powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_consistency/render.ps1 -Width 4096 -Samples 96
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_consistency/finish.ps1 -Width 4096 -Review preview4096
python -B tools/sky_consistency/make_review.py --stage preview4096
python -B tools/sky_consistency/measure_readability.py --stage preview4096
```

Review title, near/middle/far city, station, moon, cracked worlds, ringed planets,
upper sky and the panorama. All 14 retained planet/ring/moon groups must clear
the actual solid skyline by at least three degrees. `clearance.py` records and
fails that requirement; its suggested elevations never modify geometry.
`check_architecture.py` exercises every retained ordinary lot's real accumulator
geometry, lot bounds, raised geometry/UV parity and global RNG independence.
`audit_composition.py` compares the historical lot fields and hero records
exactly, allowing only the intentional architecture labels to change.

If changes are needed, edit the authoring sources and start again with authoring.
A source or texture change invalidates the master/render contracts. Once the
candidate is accepted, keep the editable master open for finalization:

```powershell
& $mcpPython -B tools/sky_consistency/mcp_call.py tools/sky_consistency/finalize_master.py
& $mcpPython -B tools/sky_consistency/mcp_call.py tools/sky_consistency/bake_native_card.py
$cardRender = Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -ArgumentList @('-b','tmp/sky_consistency/native_card_bake.blend','-P','tools/sky_consistency/render_native_card.py') -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput 'tmp/sky_consistency/native_card_render.log' -RedirectStandardError 'tmp/sky_consistency/native_card_render.err'
if ($cardRender.ExitCode -ne 0) { throw 'Native card render failed; inspect its logs' }
python -B tools/jump_title/make_sign_card.py
python -B tools/jump_title/make_sign_card.py --check

powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_consistency/render.ps1 -Width 8192 -Samples 160
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_consistency/finish.ps1 -Width 8192 -Review final
python -B tools/sky_consistency/make_review.py --stage final
python -B tools/sky_consistency/measure_readability.py --stage final
```

Finalize the main master **before** authoring the native card bake: its receipt
pins the finalized master hash. The MCP helper writes a separate bake blend;
the background renderer creates the derived PNG and permanent
`art/sky3d/sign/v11_native_lit.png` with `native_card_art.json`. The generator
then copies that reviewed image into the native model assets. Both native
image bindings must match the bake. A later source or final-master change
requires repeating the bake, render and generation sequence.

The final native bake applies response **0.06** to architectural reflected
spill while protecting the shared lettering rectangle and bright saturated
tube cores. Native `scaleRGB=16` and the common preview conversion stay fixed.
This is a material treatment, not measured native exposure parity.

Inspect the final complete view set. `preview_candidate.py` can show the 4K
candidate while the saved master renders, but replaces the studio's in-memory
scene. Only use it after finalization; the finalizer rejects a preview scene.
Then install the reviewed result, update the measured `SKY_SCORE` in
`tools/art_cohesion/verify_tower_design.js`, and make the finished HDR preview:

```powershell
python -B tools/sky_consistency/install.py
& $mcpPython -B tools/sky_consistency/mcp_call.py tools/sky_consistency/preview.py
& $mcpPython -B tools/sky_consistency/mcp_call.py tools/sky_consistency/render_preview_states.py
& $mcpPython -B tools/sky_consistency/mcp_call.py screenshot
python -B tools/sky_consistency/verify_build.py --snapshot --title-report tmp/sky_consistency/raw_8192.title.json --title-version cyber_hero_title_2 --receipt art/sky3d/consistency_review/architecture_check.json --receipt art/sky3d/consistency_review/composition_audit.json --receipt tmp/sky_consistency/skyline.json --receipt tmp/sky_consistency/clearance.json --receipt art/sky3d/consistency_review/preview.json --receipt art/sky3d/consistency_preview.blend --receipt art/sky3d/consistency_review/baseline.json
```

Include any other inspected art/brightness or viewport evidence with additional
`--receipt` arguments before snapshotting. Source hashes, images, master, paired
render/sign AOV, finish output and deployed files remain strict. Never patch a
receipt to hide a changed input. The installer refuses to run after a snapshot.

Close heavy authoring/render processes before the bake. Run the guarded FULL
build serialized, only when BlackOps3 is absent. The user playtests; do not launch
the game. After BUILD OK:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_map.ps1 > tmp/sky_consistency/full.log 2>&1
python -B tools/sky_consistency/verify_build.py --build-log tmp/sky_consistency/full.log
python -B tools/sky_consistency/make_review.py --stage final
```

Capture that guarded build's real output at `tmp/sky_consistency/full.log` using
the session's normal logging method. A later peer source change fails the default
proof. `--record-built-art` may explicitly record an earlier built-art snapshot,
but cannot waive changed sky art, deployed inputs, missing assets or stale bake.
Do not import any prior pass's peer exceptions.

The lightweight preview is `art/sky3d/consistency_preview.blend`. To reopen it,
run `tools/sky_consistency/open_preview.ps1`. Blender can reset saved viewports
to Solid during load; `activate_preview.py` restores Rendered, Scene World and
Scene Lights after checking the exact installed HDR, without resaving the blend.
Capture a reopened screenshot separately rather than overwriting snapshotted
evidence. The launcher is for the user's visible window and does not start MCP.

The shipping master now explicitly uses `sign_state: dull` for the parallel
first-jump reveal. The installer/snapshot require that actual render state.
`preview.py` imports the generated native card binary, UVs and GDT material/maps
and saves **Before jump** and **After reveal** scenes, defaulting to After reveal.
Use Blender's Scene selector or the MCP `before_jump_preview.py` /
`after_reveal_preview.py` helpers to switch without resaving. Capture those as
`blender_before_jump.png` / `blender_after_reveal.png`; the gallery shows them
separately from the dull sky-only projections. The card generator/receipt,
derived `native_card_art.json`, native outputs and preview source inputs are
pinned before building. See the review folder's `INTEGRATION.md` for display
assumptions and the frame-finish/foreground-occlusion coordination.

Blender previews approximate the established display bracket. BO3 bloom,
exposure and final visual quality remain the user's playtest. The case-safe
asteroid direction/distance fix must remain in the compiled fleet script.
