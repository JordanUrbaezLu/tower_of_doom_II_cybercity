# Sky depth and distant detail (v13)

This isolated pass improves distant architectural readability and depth while
preserving the accepted city composition, recognizable station, tall landmarks,
Dealer sign and celestial placement/radiance. All 1,189 ordinary buildings retain
the same four architecture families. Layout equality and the separate geometry
audit remain strict; surface detailing is not permission to move lots or add clutter.

The depth candidate lives only at `staged_sources/cyber_architecture.py` in this
pipeline. The live `tools/sky3d/cyber_architecture.py` remains the exact shipping
v12 source required by the existing card receipt and ordinary repository builds.
Never restore an unreviewed depth candidate over that live file. After cleaning
old modules, `author.py` explicitly loads the staged file under the module name
`cyber_architecture` in its dedicated Blender interpreter. Other local imports
still resolve from `tools/sky3d`; the staged directory is not added to `sys.path`.
`pass_config.py` follows that same resolution and hashes the actual staged bytes.
The author receipt records the resolved candidate path/hash, and the geometry
checker audits that candidate. The prior audit from when the candidate occupied
the shared path is preserved separately under `depth_review/historical/`; it is
historical evidence, not relabeled as a new staged-source check.

Stage: `tmp/sky_depth`. Review: `art/sky3d/depth_review/review.html`.
The exact prior master, EXR, stats and Blender states are preserved under `before/`
and indexed by `baseline.json`; `make_review.py` preserves matching v12 PNG views
without editing pixels. The prior Dealer native build was still pending when this
baseline was captured. Do not label it a user-verified in-game baseline.

Production stays **8192 x 4096, maximum 160 samples**. Native HDR compression,
mip/picmip exclusion, skyStops4.35 and the exact fixed gain
`0.016525428679573573` remain unchanged. `quality_profile.json` proposes adaptive
threshold .0125, minimum32, Cycles Blackman-Harris `filter_width=1.0` and OptiX RGB/albedo/normal
denoising. These settings require the owner's same-angle crop review before
production; they are not yet a measured improvement. This is Cycles' actual
`pixel_filter_type`/`filter_width`, not the separate `scene.render.filter_size`.
The profile and helper enter
the author source hashes. Author and final render receipts must contain the exact
profile, its hash and actual production scene settings. Changing the profile
requires genuine reauthoring/rerendering; never stamp an old receipt.

The original sign painting remains byte-identical `art/sky3d/sign/v12_dealer.png`.
`measure_art.py` verifies its accepted hash and exact cinematic feature anchors.
The dull shipping sky and native bright card retain the same 1536 x 1024 image
contract, 65-degree width, 11-degree title bearing and title center(768,435).
The new material/visibility bake is `art/sky3d/sign/v13_native_lit.png`, with .06
reflected architectural response and protected lettering/tube cores. Native16,
actual exported geometry/UVs and foreground holdouts remain exact. The generator
must be wired to this pass's receipt and permanent image **only after that bake
exists**. Root owns that shared `tools/jump_title/make_sign_card.py` change.

Reproduce in sequence after BlackOps3, Radiant/native compilation and every
unrelated Blender have released the machine. Keep `PYTHONDONTWRITEBYTECODE=1` and
use `-B`; the existing MCP Python below is a read-only sibling environment.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$mcpPython='../tower_of_doom_II_hellbound/tmp/gold_sword_env/Scripts/python.exe'
python -B tools/sky_depth/measure_art.py
python -B tools/sky_depth/check_depth_architecture.py
python -B tools/sky_depth/make_review.py
python -B tools/sky_depth/record_guard_evidence.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_depth/start_studio.ps1 -Mode author
& $mcpPython -B tools/sky_depth/mcp_call.py tools/sky_depth/author.py
python -B tools/sky_depth/audit_composition.py
& $mcpPython -B tools/sky_depth/mcp_call.py tools/sky_depth/finalize_master.py
& $mcpPython -B tools/sky_depth/mcp_call.py tools/sky_depth/inspect_master.py
# Close only the owned, saved studio before the sequential background crops.
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_depth/review_quality.ps1 -Case before
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_depth/review_quality.ps1 -Case after_old
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_depth/review_quality.ps1 -Case after
python -B tools/sky_depth/make_quality_review.py
```

`-Mode author` starts a factory scene, preventing unrelated preview/bake scenes
from entering the editable master. Finalize before cropping so every candidate
crop pins the exact production master. `before` versus `after_old` isolates art;
`after_old` versus `after` isolates reconstruction. Compare identical angles and
final angular texel scale. After actually reviewing them, record
`depth_review/crops/review.json` with `status:"accepted"`, the current
`profile_sha256`, exact `candidate_master_sha256`,
`reviewed_cases:["before","after_old","after"]` and a concrete `note`.
Installation and snapshot both require this current accepted review.
If the profile or art changes, reauthor, finalize and repeat all crop review.
Do not resave the production master after accepted crops. Then reopen it:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_depth/start_studio.ps1 -Mode master
& $mcpPython -B tools/sky_depth/mcp_call.py tools/sky_depth/inspect_master.py
& $mcpPython -B tools/sky_depth/mcp_call.py tools/sky_depth/skyline.py
& $mcpPython -B tools/sky_depth/mcp_call.py tools/sky_depth/clearance.py
& $mcpPython -B tools/sky_depth/mcp_call.py tools/sky_depth/bake_native_card.py
# Close only the owned, saved authoring studio before either background render.
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_depth/render_native_card.ps1
# Root now wires the shared generator to the actual depth receipt/v13 image.
python -B tools/jump_title/make_sign_card.py
python -B tools/jump_title/make_sign_card.py --check
python -B tools/jump_title/gen_fx.py --check
node tools/jump_title/test_jump_title.js
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_depth/render.ps1 -Width 8192 -Samples 160
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_depth/finish.ps1 -Width 8192 -Review final
python -B tools/sky_depth/install.py
```

Set `SKY_SCORE` in `tools/art_cohesion/verify_tower_design.js` to the measured
whole-sky score, never the nominal .64 target. Keep skyStops4.35. Review final
same-angle views. Reopen the master with `start_studio.ps1 -Mode master`, then run
`inspect_master.py`, `preview.py`, `render_preview_states.py` through the MCP
caller, in that order. Capture the viewport to `depth_review/blender_preview.png`
using the real MCP screenshot response. The preview defaults to After reveal;
`before_jump_preview.py` and `after_reveal_preview.py` switch actual saved states.
`open_preview.ps1` restores Rendered/Scene World/Scene Lights on reopen.
Run `make_review.py` again to include completed outputs. The gallery distinguishes
the dull panorama from the actual native card preview; native bloom/exposure
still require the user's playtest.

Before root's combined, serialized guarded FULL build, freeze actual inputs:

```powershell
python -B tools/sky_depth/verify_build.py --snapshot --title-report tmp/sky_depth/raw_8192.title.json --title-version cyber_hero_title_dealer_3 --receipt tmp/sky_depth/skyline.json --receipt tmp/sky_depth/clearance.json --receipt art/sky3d/sign/v12_dealer.prompt.txt --receipt art/sky3d/sign/v12_dealer.provenance.json
```

Mandatory proof includes baseline/view manifests, source-art and composition
audits, geometry/crop evidence, current resource-guard tests, actual master and
two-state preview, production render/finish/install, and derived native card.
Do not freeze while another task changes runtime inputs. Preserve any failed
snapshot/log and resolve drift; no exception list or stale-pass substitution.
After root's build, `verify_build.py --build-log <exact-root-build-log>` checks
current source/deployed parity, fresh converter/cache/probe evidence, packed
native sign geometry/material/images and private database bindings. Dealer
presence source assets remain included; its owner's separate post-build verifier
proves the three world materials/portraits. Concurrent fleet, jump and boss work
must finish its own required checks before the combined build.

All launchers use `resource_guard.ps1`: `*Radiant*`, BlackOps3, cod2map64,
linker_modtools and gdtdb block heavy work. Background render, finish and native
card wrappers monitor their owned child only; interactive studios have PID and
creation-time watchers. Other Blender processes block new launches; a peer that
appears afterward also stops only the captured sky child. MCP checks
resources before connection and each action. Use the guarded PS1 wrappers, never
the internal background Python renderer directly. `render.ps1 -CheckOnly`
performs preflight without launching Blender; `test_resource_guard.ps1` uses
synthetic process objects and never starts/stops OS processes. Record this pass's
own test/refusal results, not copied Dealer receipts. Observed editor/render
overlap could increase memory pressure; it did not prove the earlier Radiant
root cause. Never launch the game; the user playtests.
