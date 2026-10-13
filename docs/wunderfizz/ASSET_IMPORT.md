# BO6 Wunderfizz original source import

Status: **Original BO6 assets and lossless glass preserved; corrected four-haven
guarded FULL build/navigation/deployment checks passed. User playtest pending.**
Exactly four counters belong inside the existing haven domes on floors
**10, 20, 30 and 40**. Current four-haven FF: 220,396,416 bytes; 2026-10-08T15:20:49.643704-04:00; SHA256 `6adf2e8fdc9d0a86493f2a0ea8c9e822b568f3f0e8232c1e251c450af52cf554`.
Current receipts: [build/deployment](../../art/wunderfizz/build.json), [compiled assets](../../art/wunderfizz/compiled_assets.json), [native audio](../../art/wunderfizz/native_audio.json) and [fresh geometry/navigation](../../art/wunderfizz/milestones_delivery.json).

The earlier 50-counter placement was a mistake. Its completed FF at
2026-10-07T15:04:17.437771-04:00, 220,532,160 bytes, SHA256
`1f4f36b8028fdc1ced11f8d81e9e8fb0d502b3536f7257a00578942aad267ad4`,
remains [historical evidence](../../art/wunderfizz/deliveries/20261007_150417_fifty_stops_superseded/art/wunderfizz/build.json).
It proves the stated original-asset checks, not the corrected four-haven layout.
No game was launched and no native audio or animation has been heard/observed
by the agent.

The machine is WetEgg's original BO6 port supplied in KingslayerKyle's
BO6Overhaul Assets v1.0. The author's 804,084,202-byte RAR has SHA256
`3c6a12b993e32b667bdb10defc2b9392801dc1d7fd9462812b288a974088a0fa`.
It supplies the actual native BO3 machine port; no replacement model or label
redraw was generated. The former local BO6 installation is absent, so this is
author-package provenance rather than a fresh extraction from that install.

Source: [author repository](https://github.com/KingslayerKyle/BO6Overhaul),
[author asset listing](https://assets.gscode.net/assets/black-ops-6-overhaul),
[author download folder](https://drive.google.com/drive/folders/1eictKdWp20j5v7jT9h3p4Ck8F_id2KsH).

## Preserved assets and native conversion

The installed import preserves both original seven-LOD models, all twenty
4096 by 4096 source PNGs, six material definitions/shaders, geometry, labels,
UVs, normals, rig/weights, off/on states, original animation and both EFX files.
Seven original machine WAVs retain their PCM bytes and supplied seven alias
rows/four names. Native source paths are retargeted into this map's owned roots;
the manifest records all allowed image/path definition changes.

The powered model is `t10_zm_machine_wunderfizz_fxanim_on`; the off model omits
`_on`. Native scale is 1, front is +X at yaw 0, and the rear `tag_origin` remains
the floor pivot. All LODs span X `[-1.372424,51.240486]`, Y
`[-27.691320,27.691189]`, Z `[-0.001485,96.939049]`. Activation raises the top
to `97.765066` at frame 50 without increasing its XY footprint. Original lower
box/sloped upper collision spans X `[1.5,39.5]`, Y `[-22.5,22]`,
Z `0..101.472222`; the generated map stamps those original hulls.

Every image keeps mip base `1/1`, preserving the supplied 4K top mip. The
original glass diffuse PNG contains translucent and opaque 0..255 alpha. Its
author setting `compressed no alpha` would discard that channel. An interim
BC7 conversion retained alpha at the top but failed the native coarse-mip
fidelity gate. The final image definition therefore uses **uncompressed
`sRGB3chAlpha`, native IWi format 14 (RGBA8)**. No original PNG pixels, material
shader, mesh or animation were changed for this correction.

The native glass gate requires all thirteen mips, byte-exact full base RGBA
and a maximum alpha difference of one byte at every mip, including 2x2 and 1x1.
The preserved native conversion's maximum alpha error is **1 byte** across all
thirteen mips; the new build must select and verify that lossless conversion.
The lossless
chain adds approximately **64 MiB over BC7 for one shared glass texture**; all
four counters reference that texture. It is one shared chain, not four copies.
Other original textures retain their recorded native conversion settings.

## Authored animation, sound and interaction

The original 25-bone activation clip has 121 frames, 0..120 at 30 FPS. Frame 1
plays `evt_wunderfizz_activate` on `sphere_jnt` and activation FX on `body_jnt`;
frame 120 stops that effect. The alias's electricity secondary and four
authored spark emitters own their original cues. The activation EFX retains
its two original dynamic-light elements; idle EFX has no sound emitter. No
scripted duplicate activation/spark effect, sound or custom FX was added.

The replicated idle field can maintain handles on all four powered hosts.
The unchanged EFX applies native distance culling; there is no script claim
that only six idle handles exist. Separately, script arbitration permits only
nearby powered hum voices within their original 600-unit wet range, retaining
the supplied six-voice cap with only four physical counters.
Client handle generation guards and detached cleanup handle power/host loss.

Original `tag_hint` is `(50.192905,0,53.877693)` under `tag_origin`, unchanged
across off/on and all activation frames apart from float roundoff. Native use
trigger/look origin reads this tag from the spawned model. Generated +X83.240486
purchaser standing anchors remain dedicated to backend range and native nav.
They are not used as the target the player must look at.

## Receipts, gates and review limits

The current persistent source receipt is
[art/wunderfizz/asset_manifest.json](../../art/wunderfizz/asset_manifest.json),
SHA256 `994390e2f4f76763e0a17a38d7739b574460c2262d688208d97dcee5e5ebff5c`.
Its bytes pin the layout source contract. The receipt's historical staging
status is provenance, not a current build result; final build evidence belongs
in separate delivery receipts. The unmodified original GDT is under
[art/wunderfizz/source](../../art/wunderfizz/source/t10_zm_machine_wunderfizz_fxanim.original.gdt).
Audio source/PCM/alias identity is pinned by
[audio_manifest.json](../../art/wunderfizz/audio_manifest.json).

The former `tmp/wunderfizz/assets/engine_kit` and `--stage` lane are historical
import staging and may precede the lossless correction. Validate the installed
current source against the permanent receipt:

```powershell
python -B tools/wunderfizz/verify_source_assets.py
python -B tools/wunderfizz/verify_audio.py
```

The guarded build runs the native checks with its actual completed FF path:

```powershell
python -B tools/wunderfizz/verify_compiled_assets.py --ff <completed-private-FF>
python -B tools/wunderfizz/verify_audio.py --native <completed-private-FF>
```

The asset gate checks actual fourteen LODs, six complete FF materials/image
tables and native dependency bindings, original animation note payloads and
all thirteen format-14 alpha mips. Its receipt explicitly does not claim shader
constant-buffer reflection or resolved material relocation targets. The audio
gate checks native alias tables and a fresh complete loaded bank with source
PCM identity, not audible playback. Corrected native nav checks require 12
standing probes and four haven-route connections, one counter inside each
existing dome on floors 10, 20, 30 and 40. All 12 probes and four connections
passed against the fresh native mesh; FF asset/audio/deployment checks passed.
The archived mistaken 50-counter build checked 150 probes and 50 connections.

The [three-state Blender review](../../art/wunderfizz/review/review.html) is
source-art evidence for off/on/frame-50 geometry and maps. It approximates
BO3 shading and was not a native rendering test. The task-owned studio was
closed; the unrelated Blender process was preserved. Current source inspection,
motion bounds, duplicate audit and historical search evidence are linked from
[asset_inventory.json](asset_inventory.json). User verification of native
textures/glass, input, perk effects, animation/FX timing, audio and performance
remains pending.
