# Exact new Wunderfizz asset request

STATUS: superseded fallback brief. The user explicitly selected BO6, and its original author-supplied BO6 native port was obtained and staged on 2026-10-07. See [wunderfizz/ASSET_IMPORT.md](wunderfizz/ASSET_IMPORT.md). No model/art request is outstanding; guarded build and user playtest are pending.

The selected source is the BO6 Wunderfizz machine. The extraction requirements below preserve the original request history. It must retain the source game's appearance, machine labels, textures, animation and sound. The older BO3/Der Eisendrache random-bottle machine is available, but is not an acceptable substitute. This is an extraction/import request, not a generated-art brief.

The primary Cold War menu port at `kelson8/bo3-Zombies-Test-Map` identifies its machine models as `p9_sur_machine_perk` and `p9_sur_machine_perk_off`. Exact-name and variant searches of the local trees and six relevant archives did not find that model either. Its script/API behavior has not been adopted or asserted safe for this map.

Local search evidence and absolute read-only source paths are recorded in [wunderfizz/asset_inventory.json](wunderfizz/asset_inventory.json). BO6 bank metadata names six Wunderfizz ambient/spark WAVs, but those actual WAV files are absent from the local export. That metadata is included as historical reference. The BO6 author package now supplies seven actual machine WAVs, original native alias rows, and the frame-1 activation note; see the audio candidate receipt.

The zip is created by `tools/make_art_pack.ps1`. The references below are copied bank metadata for exact alias/stem identification. There is no local approved screenshot or model of the modern counter. The provider must include source-game identification screenshots with the returned original asset set; guessing an edition from metadata is insufficient.

The user's instruction to import the machine exactly takes precedence over the general art-pack typography guidance: preserve the source machine's original labels. No custom machine lettering, redesign, recoloring or generated replacement.

<!-- art-pack
name: wunderfizz_exact_import
typography: off
refs:
  docs/wunderfizz/reference/zm_perkmachine_wunderfizz.all.csv | BO6 alias-to-sound-stem metadata; actual WAVs are missing locally
  docs/wunderfizz/reference/zm_perkmachine_wunderfizz.all.json | BO6 sound-bank metadata identifying the original source bank
-->

<!-- PACK:BEGIN -->
# Exact modern Wunderfizz extraction/import

Deliver the original modern choose-perk Wunderfizz counter and its complete working asset set for Black Ops III. Keep it exactly as it appears and sounds in the selected source game. The user selected Black Ops 6. Do not replace it with the older BO3/Der Eisendrache random-bottle globe machine.

This request is for an exact game-asset extraction and faithful port. Do not generate or redesign a machine. Preserve its shape, scale, colors, labels, material wear, glass, internal detail, lights and controls. Keep the original machine lettering and symbols; no replacement typeface.

For identification only, a known Cold War port names the counter `p9_sur_machine_perk` and its unpowered twin `p9_sur_machine_perk_off`. Those models are not in our local asset library. A BO6 or BO7 extraction may use different names; identify the selected edition rather than assuming those names prove a match.

## References

Attach `reference/zm_perkmachine_wunderfizz.all.csv` and `reference/zm_perkmachine_wunderfizz.all.json` when checking BO6 sound names. They are metadata only. They do not contain playable audio and do not establish that the model has been delivered.

The BO6 metadata identifies:

| Original alias | Original sound stem |
|---|---|
| amb_perk_wunderfizz_lp | sound_369ea93cf3cc724a |
| amb_perk_wunderfizz_spark_lp | sound_28bce4d6ee02d800 |
| amb_perk_wunderfizz_spark | sound_5267732cfdd71d3 |
| amb_perk_wunderfizz_spark | sound_13c7e5b994c6fc94 |
| amb_perk_wunderfizz_spark | sound_3da1e6a1145d5a21 |
| amb_perk_wunderfizz_spark | sound_6a6565d0167835e2 |

None of those six actual WAVs is available in the local export. Include them if BO6 is the selected edition, together with every other machine activation, purchase, dispense, shutdown and refusal sound used by that edition. Do not rename a different sound to fill a missing stem.

## Required delivery

Deliver one zip named `wunderfizz_exact_source.zip` with these folders and files. Preserve all original source filenames inside the folders.

| Deliverable | Contents |
|---|---|
| `source_identity.md` | Game/edition, machine asset names, extraction tool/version, complete export steps and all included dependency paths. State any missing dependencies explicitly. |
| `model/` | Untouched original model/rig, every original LOD, UVs, vertex normals, skin weights and tags. Provide the native export and an editable interchange export where possible. Include the complete machine and every animated subassembly. |
| `materials/` | Every material definition plus its slot-to-image mapping and shader semantics. Include all color, normal, gloss/roughness, specular/metalness, AO, opacity, emission and detail maps referenced by any LOD. Keep original resolution and alpha. |
| `states/` | Original powered and unpowered appearance; ready, busy and dispense states as applicable. Supply their native state materials/parameters or full model twins, with a state mapping. Do not fake a powered appearance with a brighter overall texture. |
| `animations/` | Original idle, activation, interaction, dispense and shutdown clips where the original has them, with frame rate, looping flags, tag names, notetracks and audio timing. If a state has no source animation, say so rather than inventing a clip. |
| `sounds/` | Actual lossless WAV sources and the original alias table: channels, loop/stream flags, distance ranges, volumes and notetrack timing. Include machine-specific ambient, spark, activation, purchase and dispense audio. Metadata alone is not sound. |
| `collision/` | Original collision asset plus measured model bounds, origin/pivot, unit scale, front-facing axis, dispensing tag and interaction point. Provide a top/front/side measurement sheet. |
| `bo3_port/` | Complete compatible model, material, image, animation and sound definitions if an existing faithful BO3 port is available. Keep original sources alongside it. Identify every compatibility change. |
| `review/` | Source-game and port screenshots: front, rear, side, glass/internal details and all visible states, both close and at ordinary player distance. Include one short video demonstrating original machine motion and sound. |
| `manifest.sha256` | SHA256 hashes for every delivered file. |

## Port requirements

- Preserve original geometry, UVs, original texture appearance and state changes. Fix compatibility in the port without painting over missing assets.
- Every LOD must retain all connected visible parts and correct materials. Include any material that appears only in a distant LOD.
- Transparent covers must expose their intended internals. Bind alpha and specular images to the semantics the actual BO3 shader expects. A scalar-mask specular slot needs a linear scalar mask; do not bind a full-color specular image to it.
- Include a complete linked material definition and texture table. A name in an asset list does not prove a working material.
- Original emission maps must be present, with the unpowered state correctly dark. Do not replace missing emission with an arbitrary brightness increase.
- Preserve original animations and audio timing. Deliver real WAVs and aliases, not only sound-bank indices.
- Give original bounds and front direction before any level placement. Do not resize or reorient the original source to fit a guessed pocket.
- Keep missing source parts visible in `source_identity.md`; never silently substitute stock textures, old-machine sounds or a different model.

## Delivery checklist

- Source-game edition is identified and matches the selected modern counter.
- Every model material and animation dependency has a delivered file.
- All original LODs, UVs, normals, tags and visible parts are retained.
- Both powered and unpowered appearances are supplied.
- All original audio files and alias/notetrack timing are supplied.
- Glass reveals the mechanism and has the correct alpha/specular semantics.
- Bounds, unit scale, front axis, collision and interaction point are measured.
- Source and port screenshots/video show the same machine, with no missing textures.
- A hash manifest and reproducible export steps are included.

Return the complete original asset set. If extraction cannot supply part of it, list that missing part precisely so it can be obtained before delivery.
<!-- PACK:END -->
