# September 29 alarm surface detail

Both crown alarm sizes and the separate pressable alarm button have a material
detail pass authored through actual Blender MCP. This is a source/material
review, not a BO3 screenshot or native visual approval.

The old material tiles were almost uniform and used flat specular maps. The
new atlases give each modeled part its own region: small exposed-edge enamel
chips, contact dirt at seals, selective fastener oxidation, broken machining
scuffs, rubbed red polymer, and fine polycarbonate cleaning marks. Intact
surfaces stay relatively clean; damage follows construction and use.

Geometry, every LOD triangle/normal/weight, origin, reflector pivot, enlarged
high-fixture shape, material names, light intensity and state timing remain
the same. The lens alone selects the native advanced transparent shader sibling
so its gloss map reaches the game (the earlier basic shader ignored it).
Its color, normal and gloss maps are packed. The native compiled shader omits
the declared specular image and uses constant dielectric reflectance 0.04;
the corrected Blender lens does the same. All other GDT fields stay unchanged.
The cap's existing emissive on-state
remains; the removed floating red attract-glow is not reintroduced.

`before.png` and `after.png` use matched cameras, lights, exposure and the same
native-map preview. `detail.png` and `on_detail.png` inspect fine wear and the
active state. Opaque materials bind all four maps in the Blender master.
The transparent lens binds color, normal and gloss with constant specular 0.04.
The fullspec diffuse/GGX view and gloss-exponent conversion follow the shared
`tools/art_cohesion/native_preview.py` approximation; Blender does not match
BO3 probes, BRDF, exposure or bloom exactly.

Reproduce with Blender 4.2 and the existing dedicated MCP clients:

1. `tools/crown_alarm/mcp_call.py tools/crown_alarm/12_surface_realism.py`
2. `tools/alarm_button/mcp_call.py tools/alarm_button/02_surface_realism.py`
3. `python -B tools/crown_alarm/verify_surface_realism.py --staged`
4. Inspect matched renders and detail views under `tmp/alarm_realism/staged`.
5. In the coordinated idle window, run `tools/crown_alarm/install_surface_realism.py`.
6. Run the parent's guarded FULL build, then crown alarm compiled-LOD/source
   checks and the button's compiled mesh coverage check.

Original masters, exported UV meshes and textures are preserved in each
family's `realism_before` folder after installation. Staging always starts
from those originals, so rerunning does not repeatedly transform UVs.

`lens_native_channels.json` and the accompanying native shader disassembly
document the precise lens exception. Its 3,392 sampled face-centroid specular
pixels are uniform; that unused image carries no wear pattern. Actual lens
imperfections come from the packed color, normal and gloss maps. The shader's
declaration through `specular_base` is insufficient evidence of consumption;
its compiled resource table does not bind `specColorMap` or `specColorTint`.
The preview-only correction is reproducible through MCP with
`tools/crown_alarm/16_native_lens_preview.py`; it verifies native input hashes
are unchanged. Preview helpers display the preserved repo render paths.

`source_validation.json` proves the exported mesh structure is identical
apart from UV coordinates. `authoring_receipt.json` records source captures.
Native appearance is for the user's playtest. No game was launched.
