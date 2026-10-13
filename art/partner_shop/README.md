# The Black Market (was the Item Shop): Blender master and native crown-room test

**2026-09-29: THE BLACK MARKET SIGN (user: "The Item Shop / Black Market is confusing. Lets just
rename it Black Market all together and update the model with Blender MCP").** The neon sign now
reads **BLACK MARKET**, rebuilt through the MCP studio by `tools/partner_shop/18_black_market_sign.py`.
It uses the same construction as before: a luminous tube on a charcoal glass bedding, electrodes with
return leads, glass standoffs and brass clips. The sign is one line of condensed letters (5.7 x 11)
inside the unchanged border. The two words keep the old reds: BLACK crimson, MARKET orange-red.
**C, E and T blink** on the shared fault bus. They fill the three native blink slots: `letter_t` and
`letter_e` keep their letters, and `letter_c` replaces `letter_h`. The three sign sparks moved with
their letters: T 31, E 91, C 151. The counter stencils now read NO QUESTIONS ASKED and
SPIN / SOCKET / SCRAP (the Black Market's actual verbs). The prior master is kept as
`checkpoints/20260929_before_black_market.blend`. `write_timing.py` regenerates the client timing
script and the audio manifest's spark sites without rewriting any sound files.
BUILT in session fd's FULL BUILD OK 14:26 (tmp/spire_removal/full1.log), FF 216,215,232 B at 14:23:04:
`SHOP_NATIVE_VALIDATED 19 models; 133 LOD files; compiled=True`; every shop input deployed = repo. UNPLAYED.


Latest saved studio session (September 24, 22:24):
[complete session](checkpoints/20260924_222403_saved_session.blend).
Saved through Blender MCP, reopened successfully with 929 objects, then
closed at the user's request. The exported `partner_shop.blend` is preserved.

Tower II only. Authored in the visible Blender MCP studio on port **9881**.
Native integration is authored; build evidence lives in `tmp/partner_shop_build/`.
Native appearance and audio await the user's playtest. This pass implements
appearance, power states, location switching, effects and audio. Partner upgrade
stock, prices and purchases have not been designed or added.

## Current design

Blackened metal, oxblood panels, red neon and subdued amber instruments.
Detailed inventory, rear service door, roof collector, left capacitor bay,
copper pressure piping, cooling fins and wiring. The small counter hand is
robotic merchandise; the merchant's own hands hang below the counter.

The shorter black-hooded merchant has slanted red X eyes, overhanging armored
brows, angular cheek plates and a jagged, uneven toothed grin. The mask pulses
smoothly over six seconds, independently of every electrical flash.
All **BLACK MARKET** letters work: only **C, E, T** blink briefly;
B, L, A, K, M, R stay steady. No permanently dead letters remain.
Canisters breathe in phase over three seconds, with four chasing bands on the left.
The three blinking letters and all canisters share one dropout/recovery timeline.
The pressure wheel turns through **100 degrees** and returns; an ivory rim index
makes the travel readable. The gauge swings +/-24 degrees with fine chatter.
Ten larger localized spark bursts form three fault clusters per six-second loop,
at frames 31, 91 and 151. Both side canisters spark in each cluster. Arcs span
roughly twice the former distance; flecks are larger and travel farther.
The user's WAV supplies one crackle per cluster, avoiding stacked simultaneous audio.

Set the master scene's `shop_powered` custom property to 0 for the off state:
merchant absent, emission/practicals/sparks disabled, valve and needle at rest.
Physical equipment remains. Set it to 1 for active animation.

## Review artifacts

- `review.html`: gallery and `electrical_preview.mp4`, six seconds with audio.
- `pressure_preview.mp4`: the same six-second timeline, focused on the valve
  and right container. Render with `17_pressure_preview.py` and mux the same WAV.
- `hero.png`, `powered_off.png`: active/off art master renders.
- `player_view.png`, `merchant.png`, `rear.png`, `left_detail.png`,
  `pressure_detail.png`, `pressure_sparks.png`: detail views.
- `native_baked.png`, `native_baked_off.png`: actual reduced geometry and
  baked maps reconstructed in Blender, **not BO3 screenshots**.
- `electrical_timing.json`, `electrical_evaluated.json`, `neon_timing.json`, `audio_manifest.json`:
  timing and WAV provenance. Frame 181 closes onto frame 1, at 30 fps.
- `engine_kit/`: source/install manifests, seven LODs per component and checks.
- `references/`: three user screenshots and original downloaded WAV.
- `checkpoints/before_electrical_detail.blend` and
  `checkpoints/20260924_before_shared_fault.blend`: preserved prior art.
  The old `neon_preview.mp4` and `sign_frames/` are historical.

## Reproduction

Use the existing MCP Python environment read-only with bytecode disabled:
`../tower_of_doom_II_hellbound/tmp/gold_sword_env/Scripts/python.exe`.
`tools/partner_shop/mcp_call.py` uses a real upstream MCP ClientSession,
connecting to `127.0.0.1:9881`; the separate teleporter studio is 9879.
Start the shop with Blender's `--factory-startup --python
tools/partner_shop/mcp_bootstrap.py` if needed.

Send scripts through `mcp_call.py` in this order:
`01_structure.py`, `03_hardware.py`, `04_masked_merchant.py`,
`06_neon_sign.py`, `07_dark_direction.py`, `10_electrical_detail.py`,
`11_power_states.py`, `12_pressure_valve.py`, `16_fault_and_mask.py`,
`18_black_market_sign.py`, then `14_validate_live.py` (live checks; writes
`electrical_evaluated.json`) and `python tools/partner_shop/write_timing.py`.
`19_view_*.py` frame review screenshots (`mcp_call.py screenshot`).
The first human-face study and `08_review_assets.py` are superseded;
do not use their timing as the final pass. `13_render_review.py` renders
stills and every animation frame in background Blender.

Run `export_native.py` in background Blender, then `install_native.py`
and `audio_fx.py` in Python for native assets. `render_native.py` reviews
the actual reduced geometry and maps. Build gates include
`verify_native.py` and `test_shop.js`. Asset changes require a full
guarded build. Never write to another map or through stock-source junctions.

## Native contract

One Blender unit = one BO3 inch; origin is the floor, front is **-Y**.
The generator owns west/east/north crown anchors and four collision boxes each.
One shop activates when power and round state are ready. The stated visual-test
default cycles west -> east -> north on round changes. This is not a finalized
purchase/mystery-box movement rule. `activate(index, reason)` owns transitions;
-1 powers all off. Catalogue and purchases are separate future work.

Only the active shop has the merchant and 14 other controllable components.
Off meshes retain physical neon/canisters with emission disabled. Handoffs
clear clientfields, allow two snapshots, delete active pieces and restore
off bodies before enabling the next. Allocation failure rolls back to off.
End-game and host loss have explicit cleanup.

Client `_tod_shop.csc` drives the shipped material's real `hdrScale`
constant using server time. Sign, mask, canister scans and sparks share a
six-second clock. Each sound and spark starts in the same client callback,
at the same world origin. Native arc/fleck models come from Blender meshes.
Two one-shot emitters produce six particles/event, at most 24 overlapping,
maximum lifetime 310 ms, no custom dynamic lights. Stock Wunderfizz
`zombie/fx_wonder_fizz_lightning_all` attaches only to the active shop;
its cost/appearance are additional and remain unmeasured.

19 native models, seven LODs each; four materials, fifteen maps
(body 4096, vendor 2048, glow palette 64).
`[TOD_SHOP]` logs placement/state/failure/cleanup;
`[TOD_SHOP_C]` logs marker initialization and the first ten synchronized
bursts per activation. Normal dev mode enables logs; temporary
`TOD_SHOP_LOG 1` also captures this normal-match bring-up. Zero it after
acceptance. The user tests; archive via `tools/capture_ai_logs.ps1`.

Full build and deployment verified September 24, 15:05 Eastern: all 19
models / 133 LODs match native geometry; all expected art, FX and sounds
are packed. The combined 351-input snapshot matches deployment, including
the concurrent darker hall and sky. FF 210,979,392 bytes, timestamp 15:03:33.
Evidence is in `tmp/partner_shop_build/revision2/` (final_full_build.log,
deployment.json and final_build_record.json). Full build 10 first validated
the shop; the follow-up dark-hall build carries both sets of changes.
The live MCP preview remains open and playing, with the exported master unchanged.
No game launch; native appearance/audio and runtime logs await the user.
