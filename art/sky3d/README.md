# Rendered Cybercity sky

Run [open_preview.ps1](../../tools/sky_consistency/open_preview.ps1) to open
[consistency_preview.blend](consistency_preview.blend) with the installed
finished panorama. The launcher restores **Rendered**, **Scene World** and
**Scene Lights** after loading; opening the blend directly can reset it to Solid
and show a blank gray viewport. Numpad 0 returns to the camera. This lightweight scene
uses the exported HDR and the review images' approximate display bracket. Its
Scene selector switches between **Before jump** (dull shipping sky) and
**After reveal** (the native lit sign card, selected by default). The card uses
the actual generated geometry, UVs, texture and material scale. BO3 bloom,
exposure, transparency and visual quality remain the user's playtest; this
revision has not been played in the native game.

The current art follows the user's [approved middle-ground concept](middle_ground_review/concept.png):
engineered pylons, dimensional metal lettering and a smaller mechanical death-mask.
All **1,189 ordinary buildings** now use tapered, split and cantilevered cyber
forms with worn armor panels, recesses, varied roughness and inset light
channels. Elevated pods use the same kit. Near and distant buildings, the
32 large landmarks and the sign frame share the worn graphite/alloy treatment.
The moderate reduction, station, eight preferred tall hero towers and measured
planet/ring/moon clearance are preserved. Planet and star radiance is reduced
locally to reveal surface detail; fixed finishing gain preserves the approved
near-city brightness.

[Final images and comparison](consistency_review/review.html) collect the art
and evidence. [Preview settings](consistency_review/preview.json) identify the
exact HDR and native inputs. The [After reveal render](consistency_review/blender_after_reveal.png)
and [Before jump render](consistency_review/blender_before_jump.png) show the two
states at the same camera; [render evidence](consistency_review/state_renders.json)
pins their saved preview. [Activation evidence](consistency_review/preview_activation.json)
records the launcher settings without resaving the preview asset.
The guarded FULL build passed on 2026-09-30 at 11:26; the current
[build receipt](consistency_review/build.json) proves 212 matching runtime
inputs, 111 authoring artifacts, fresh sky/probe lighting, and the compiled sign
model/material/image. Current source parity passes. Native appearance awaits
the user.

The sign's [source artwork](sign/v10_cyber_hero.png), [exact prompt](sign/v10_cyber_hero.prompt.txt)
and [provenance](sign/v10_cyber_hero.provenance.json) retain the built-in Imagegen
extraction of the approved concept. Its generated pixels/alpha are unchanged.
`cyber_hero_title.py` packs the artwork, authors sparse card geometry and calibrates
its dark metal/colored emission. Its measured features also place the jump glows.
The shipping sky bakes the dull sign; the native card lights it after the crash.
The [derived lit texture](sign/v11_native_lit.png) applies the shared frame finish
and true foreground holdouts without editing the original painting. Its final
0.06 reflected-spill response keeps the frame dark while protecting lettering
and bright tube cores at native scale 16. [Integration details](consistency_review/INTEGRATION.md)
and the [material-bake receipt](consistency_review/native_card_art.json) record
the source bindings and approximate display assumptions.

[tod2_sky.blend](tod2_sky.blend) is the editable full generator output. Regenerate
through [the Blender MCP pipeline](../../tools/sky_consistency/README.md); manual
master edits do not survive regeneration. Architecture comes from
`cyber_architecture.py` and `cyber_coverage.py`, the station from `cyber_station.py`.
[Docs/166 section 13](../../docs/166_sky3d_rendered_sky.md#13-shared-city-architecture-and-readable-celestial-surfaces-2026-09-30)
records the revision.
Static ships/asteroids remain retired; the separate moving native fleet and its
case-safe asteroid fix remain intact.

The [v8 gallery](cohesion_review/index.html), [v9 gallery](simplify_review/review.html)
and [v10 middle-ground gallery](middle_ground_review/final_review.html), with their
preview files, are historical. The v9 gothic gate overcorrected the weak v8
monument; the approved middle ground remains the design baseline.

`billboards/` holds the docs/167 image-model ad screens (delivered 2026-09-25: `ad_01..12.png`, the drop box-filtered to
512 px on the long side - a screen is 2..9 texels tall in the 8192 ship). `render_sky3d.ps1` uses the folder by default;
`-ScreensDir none` renders the procedural mosaic only. The originals stay in the Downloads zip.

`sign/` retains the historical title gate (v7, 2026-09-29, docs/166 Â§9), available only through `--sign-style gate`: the user's reference painting (`tod2_title_gate_reference.png`), the two BiRefNet-DIS5K masks cut from it (`_dis5k_1024/2048.png`, `tools/sky3d/segment_title_gate.py`), and its generated card assets: `tod2_title_gate.png` (RGBA), `tod2_title_gate_glow.png` (the neon's glow, added light) and `tod2_title_gate.json` (padding + the text box centre). The card files are GENERATED by `tools/sky3d/cut_title_gate.py` â€” change its polygons and re-run it, never paint the PNGs by hand.
