# Clear alarm glass ? 2026-10-01

The reported defect is the glass cover: the player cannot see the mechanism
inside even though its light passes through. The native lens material used a
full-color `specularMap` image where the advanced transparent shader requires a
linear scalar `specularMask`. BO3 rejected the definition and packed only an empty
reference in the playable map. A material name in a dependency ledger did not
prove that its definition was usable.

The isolated native probe reproduces that rejection with the original binding.
Changing only the lens `specColorMap` to the compatible stock `$black_specular`
produces a complete material with an eleven-image native table. Positive and
negative controls rule out zero emission and shadow flags as the cause. This
binding preserves the red surface, zero glass self-emission, native blend/depth
state, normal/gloss detail and dielectric F0=.04.

The cover also had alpha82/255 across used texels, thirteen overlapping optical
ribs at LOD0 and opaque unused atlas space. Source/deployed parity, native UV
coverage and decoding the actual selected BC7 image proved that the original
alpha was present. The repair sets dome alpha=.10, ribs=.05 and unused padding
alpha=.045. RGB, the other 27 crown maps, all 15 crown native binaries, alarm
button assets, rotation and lighting remain unchanged. The lens-only native tint
is bounded to `.220916 .220916 .220916 1`; its black scalar mask produces F0=.04.

The earlier gray32-as-specular-mask inference was incorrect. Gray32 is the
thermal heatmap; an invalid material has no verified native specular binding or
before-F0. The corrected audit retains that history explicitly as an error.
The six actual transparent pixel shaders have no discard instruction. Their
ordinary lit state uses SrcAlpha/InvSrcAlpha and disables depth writes.

[Close, distance and rotating-light review](../../art/crown_alarm/lens_review/review.html)
uses the actual unchanged exported housing and rotor. Its left comparison
reconstructs the original alpha with the repaired valid shader; it does not
reconstruct the game's old fallback material. The saved native preview hides
duplicate authoring meshes, opens in Rendered shading with scene lights and
animates the exported rotor at its 1.5 second cadence. Blender BRDF and bloom
remain approximations; final appearance is the user's native playtest.

Reproduction and delivery checks:

1. `prepare_lens_repair.py` captures current shipping inputs under
   `tmp/alarm_lens_repair`, including the alarm package. It refuses to replace
   an existing capture or overwrite changed assets.
2. The owned studio and actual Blender MCP run `17_clear_lens.py` and
   `18_finish_lens_preview.py` against that isolated capture. The revised
   binding candidate was reviewed through `19_review_binding_candidate.py`
   before publishing its authoring sources.
3. `lens_repair_gate.py --staged` requires unchanged native geometry, UVs, states,
   lighting and RGB, exact lens-only material changes, transparent filtered UVs
   across six housing LODs, and matching map hashes. Negative controls reject
   unrelated edits, invalid masks and added emission.
4. The first candidate's original capture remains intact. The binding follow-up
   uses `publish_lens_binding.py --capture` and then `publish_lens_binding.py` to
   require the exact previously installed live hashes before publishing the
   complete rerendered source/art/receipt set.
5. Run the guarded FULL `tools/build_map.ps1`. Its alarm gate reads the actual
   fastfile material definition and dependency-selected BC7 cache across all
   eleven mip levels; reference-only materials are a failure.
6. `record_lens_build.py` records fresh shipping outputs and exact deployment
   parity in `art/crown_alarm/lens_review/build.json` only after BUILD OK.

Use `tools/crown_alarm/open_lens_preview.ps1` after the build. It guards against
active game/editor/native stages and other Blender processes. No game is
launched by this workflow. Native visual approval remains pending the user.
The launcher verifies the reviewed blend hash and explicitly restores Rendered
shading, scene lights/world and the camera in every live viewport after loading.
This handles startup UI preferences that can otherwise open the file in Solid
mode. It does not resave or alter the reviewed scene.

Delivered 2026-10-01 at 13:29 EDT: the guarded FULL build finished successfully.
Its fastfile is 228,267,904 bytes, modified at 13:27:40, SHA256
`4dcd32a82e8151315bcef3f09c11c334fd8ae7a3b1f551cddf4a4a05abcf3a1b`.
The complete native glass definition and eleven-image table passed verification;
all eleven converted BC7 mip levels and six housing LODs passed with at most one
byte of alpha error. The build checked all eighteen compiled alarm LODs; the
delivery receipt pins 81 runtime files to their identical deployed copies.
Geometry and lighting were reused. The build added no new linker errors.
[Build receipt](../../art/crown_alarm/lens_review/build.json),
[compiled material proof](../../art/crown_alarm/lens_review/compiled_material.json)
and [compiled image proof](../../art/crown_alarm/lens_review/compiled_image.json)
record this delivery. A peer's later relink may replace the fastfile; it must keep
the repaired source set and run the native glass gates. No game was launched.
The exact full-build receipt, compiled proofs and transcript are also retained
under `art/crown_alarm/lens_review/deliveries/20261001_132740/`, so a later build
can refresh the current compiled checks without erasing this delivery's evidence.

The subsequent VO relink also finished BUILD OK and reran both native glass
gates successfully. The current FF is 228,267,904 bytes at 13:41:29, SHA256
`33cfbc45696a14eb919a53e740d8aa7d3053f96db6d7317d733e64e49a2dc912`.
[Relink proof](../../art/crown_alarm/lens_review/peer_relink.json) identifies its
current compiled checks. The correct live Rendered preview was confirmed by
capturing the actual owned Blender window, retained as
[visible preview](../../art/crown_alarm/lens_review/visible_preview.png) and
[activation proof](../../art/crown_alarm/lens_review/visible_preview.json).
MCP's offscreen Cycles screenshot was effectively blank; the actual window
showed the red transparent cover and its internals correctly. Blender remains
an approximation, with native visual approval still pending the user's test.
