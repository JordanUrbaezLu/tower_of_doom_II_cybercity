# Black Market dealer crest

The user accepted the v11 city and asked for the skull above the sky title to
resemble the Black Market dealer, who will be the final boss. This pass changes
that crest to the established dark hood, red X eyes and stitched grin. It retains
the accepted massive lettering, worn cyber frame, all city composition records,
restrained celestial emission, fixed finish gain and dull-before/bright-after
first-jump presentation. Final-boss gameplay and map presences have separate owners.

Imagegen source: `art/sky3d/sign/v12_dealer.png`; prompt/provenance beside it.
`measure_art.py` reads the before/after images without editing them. Imagegen
changed texture pixels beyond the crest, so exact original pixels are **not**
claimed. Title, subtitle and both frame sides register at zero pixel translation;
source brightness stays within 1.3%. The three cinematic crest features were
remeasured from their near-white tube cores; title/subtitle anchors stay fixed.

The sky and native bright card use the same source, 1536×1024 contract, 65-degree
width, 11-degree title bearing and source title center (768,435). The native card
retains the shared graphite response, .06 reflected-frame response, native16
emission and true scene-depth holdouts. It has two triangles. Foreground visibility
comes from a real Blender material bake; no source image pixels are edited by Python.

The isolated master/stage is `tmp/sky_dealer`; evidence is
`art/sky3d/dealer_review`. The v11 review/stage remains historical and untouched.
The common installed master remains `art/sky3d/tod2_sky.blend`.

Reproduction, in order (MCP Python is the existing read-only sibling environment;
always use `-B` and `PYTHONDONTWRITEBYTECODE=1`):

```powershell
python -B tools/sky_dealer/measure_art.py
& $mcpPython -B tools/sky_dealer/mcp_call.py tools/sky_dealer/author.py
python -B tools/sky_dealer/audit_composition.py
& $mcpPython -B tools/sky_dealer/mcp_call.py tools/sky_dealer/finalize_master.py
& $mcpPython -B tools/sky_dealer/mcp_call.py tools/sky_dealer/bake_native_card.py
& $mcpPython -B tools/sky_dealer/mcp_call.py tools/sky_dealer/skyline.py
& $mcpPython -B tools/sky_dealer/mcp_call.py tools/sky_dealer/clearance.py
# Close the saved authoring studio before background rendering.
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_dealer/render_native_card.ps1
python -B tools/jump_title/make_sign_card.py
python -B tools/jump_title/gen_fx.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_dealer/render.ps1 -Width 8192 -Samples 160
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_dealer/finish.ps1 -Width 8192 -Review final
python -B tools/sky_dealer/install.py
```

Set `SKY_SCORE` in `tools/art_cohesion/verify_tower_design.js` to the **measured**
whole-sky score; retain skyStops4.35. Then author the preview through the actual
MCP studio (`start_studio.ps1 -Mode master`) in one sequential session:
`inspect_master.py`, then `preview.py`, then render both states with `render_preview_states.py`,
and capture the viewport. The preview defaults to After reveal. Reopen it with
`open_preview.ps1` so Blender restores Rendered/Scene World/Scene Lights after load.

Before root's serialized guarded FULL build, freeze the actual inputs:

```powershell
python -B tools/sky_dealer/verify_build.py --snapshot --title-report tmp/sky_dealer/raw_8192.title.json --title-version cyber_hero_title_dealer_3 --receipt art/sky3d/dealer_review/art_measurements.json --receipt art/sky3d/dealer_review/composition_audit.json --receipt tmp/sky_dealer/skyline.json --receipt tmp/sky_dealer/clearance.json --receipt art/sky3d/dealer_review/baseline.json --receipt art/sky3d/sign/v12_dealer.prompt.txt --receipt art/sky3d/sign/v12_dealer.provenance.json
```

After the guarded build, `verify_build.py --build-log <exact-root-build-log>` proves
the same captured/deployed/runtime inputs and native card coverage. Do not freeze
early while another task is changing runtime inputs, and never overwrite a failed
snapshot to hide source drift. Keep renders serialized on this 16GB machine and
stop heavy rendering for a user match. `render.ps1` also refuses while any process
name matches `Radiant*` (including `Radiant_modtools`). If one starts during a
render, it stops only its owned Blender process, leaves Radiant alone, preserves
stage/log files and fails clearly. This follows the observed concurrent Map One
Radiant build and possible added memory pressure; `radiant_guard.json` records a real refusal
test without launching Blender. All launchers use `resource_guard.ps1`: broad
`*Radiant*`, BlackOps3 and the guarded build's native compiler list (`cod2map64`,
`linker_modtools`, `gdtdb`). The render wrapper monitors the same set during its
run. Finish and native-card rendering use the same owned-child monitor, including
a fresh check immediately before launch after any long hashing. The direct
native-card entry point is `render_native_card.ps1`; do not invoke the internal
Blender renderer directly. Renderer files that produced the accepted outputs
remain unchanged so their original provenance stays truthful.

Both interactive launchers require the other Blender slot to be free and start a
watcher tied to the captured Blender PID **and creation time**. It exits with that
studio and stops only that studio if game/editor/native work begins. The MCP
caller rechecks resources before connecting and immediately before each action.
`render.ps1 -CheckOnly` tests the real preflight and never launches Blender, even
if no blocker remains. `test_resource_guard.ps1` exercises each name and unrelated
negative controls without creating or stopping OS processes; `resource_guard.json`
records that result plus the live preflight. The observed concurrent editor/render
overlap could have increased memory pressure; its role in the reported Radiant
issue is unproven. Never launch the game; the user playtests.

Source/runtime checks: `make_sign_card.py --check`, `gen_fx.py --check`,
`node tools/jump_title/test_jump_title.js`, registration and composition checks,
celestial skyline clearance, exact final render/finish/install receipts and
strict post-build verification. Visual preview is evidence of Blender output,
not a claim about final native BO3 bloom or exposure.
