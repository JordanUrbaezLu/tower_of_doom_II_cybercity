# September 29 surface realism pass

User request: every new model should carry believable material variation and
small imperfections, consistent with Black Ops III. This pass covers the eight
spacecraft, seven asteroid variants, crown alarms, alarm button, wormhole rifts
and shooting stars. The permanent checklist is in CLAUDE.md's quality section
and is linked from AGENTS.md.

The visual intent is subtle use and age: exposed alloy on worn paint edges,
residue in joints, handled controls, heat-touched engine metal and fractured,
mineral-bearing rock. Different materials need different marks. Readable
silhouettes, the existing lighting hierarchy and clear gameplay states matter
more than covering an object with noise.

## Review

- Fleet and asteroids: [all variants and matched comparisons](../../art/sky_ships/review/realism/index.html).
- Alarm and button: `art/crown_alarm/realism_review/` and
  `art/alarm_button/realism_review/` contain matched before/after and close views.
- Sky effect sprite sources and phase preview: `art/sky_fx_detail/`.
  These are the authored detail layers, not a complete BO3 effect render.

Blender uses the exported color/normal/specular/gloss maps. The fleet preview
also uses the map's actual Cybercity panorama. The native fullspec/GGX preview
is an approximation; it does not reproduce BO3 probes, exposure, particle
sorting, distortion or bloom exactly. The user judges the built result.

The alarm lens uses BO3's advanced transparent shader: its color, normal and
gloss maps are packed. Compiled shader inspection showed fixed dielectric
reflectance rather than an RGB specular texture; `i_tod_alarm_lens_s` remains
source art only. The lens preview uses the native 0.04 reflection value. All
other required map channels remain part of the build audit.

## Effects

`tools/sky_fx_detail/01_author.py` through `06_black_export.py` run through the
actual Blender MCP studio on port 9894. They create editable curves, render
their alpha/color textures, keep the source `.blend`, render a nine-frame
detail-layer preview and export the black aperture with dithering disabled.
Outputs are staged in `tmp/sky_fx_detail/staged` until inspected.

`tools/sky_fx_detail/native_detail.py` refines the existing sky generator output:
fine torn orbital filaments, faint accretion wisps, a black absorbing aperture
and irregular ion threads in meteor trails. Stock animated flow, lightning,
distortion, motion and sounds remain part of the composition. The white opening
seed fades before emergence, and fewer overlapping particles preserve detail.
The pass adds no effect hosts, emitter elements or dynamic lights.

The native textures are straight-alpha PNGs; the image converter is explicitly
set to premultiply. The aperture is black RGB with soft alpha under a blended
shader, not an additive black sprite. Its small footprint stays inside the
fine rim. Single-frame custom maps reset every inherited flipbook field;
the retained stock swirl keeps its real animated atlas. Meteor art repeats
along U, with transparent V borders and the original native trail geometry.

`check_effects.py` enforces effect names, element counts/types, bounding boxes,
child references, ownership, trail settings, atlas state and particle caps.
Its negative controls reject an inherited animated atlas and an extra emitter.
`native_detail.py --ledger <assetinfo.csv>` also checks the four authored images
and materials in the native build. Existing `[TOD_SKY]`, `[TOD_CROWN_ALARM]` and
alarm-button logs remain the playtest diagnostics; this surface-only pass adds
no per-frame logging.

## Build and test status

The art requires a FULL guarded build. `tools/realism_pass/verify_build.py
--snapshot` records the exact inputs immediately before it, and `--build-log`
checks the completed fastfile, packed art, matching deployment and source
freshness. Evidence lives in `art/realism_pass/build.json` when the audit passes.

The FULL art build completed at 18:25 on September 29. A peer's later luck-script
change completed a serialized script-only relink at 18:36. The original full-build snapshot,
log and fastfile identity are preserved in `art/realism_pass/full_artifact.json`.
`--base-full-artifact art/realism_pass/full_artifact.json` lets the audit verify
the later relink only when every owned art input is identical to that full build.
The completed relink's 405 deployed inputs match its captured snapshot; all 209
art inputs remain identical to the full build. The audit found all 178 required
art assets and 65 sky effects, including nine button LOD entries.

Additional peer luck work began after that relink. `--record-built-art` records
this boundary explicitly: all owned art must still match, the deployed tree must
match the build snapshot, and only shared-source edits made after the fastfile
may be reported as pending. The receipt sets `current_source_parity=false` and
lists their paths, timestamps and old/new hashes. It never syncs later work or
claims it was included. The ordinary audit remains strict without that option.

Native visual approval is pending the user's playtest. No game is launched by
this workflow. Check the button at use distance and in its pressed state, alarm
lenses off/on, a passing ship's underside/engines, tumbling asteroid highlights,
rift emergence/collapse, and meteor trails against both bright and dark sky.
