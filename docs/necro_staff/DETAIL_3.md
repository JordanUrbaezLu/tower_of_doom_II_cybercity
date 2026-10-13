# Staff detail pass 3

The user asked for substantially more detail after rejecting the first in-game
staffs. This pass builds on the straight shaft, corrected Tier 2 ferrule, exclusive
skull atlas and repaired Soul Pulse described in [iteration 2](ITERATION_2.md).

Tier 2 keeps the simple silhouette. Tier 3 retains the screenshot's spiked halo,
long central blade and forked neck. Added detail is carried by exported geometry
and native texture maps:

- Recessed, bevel-edged channels cut into all 11 Tier 3 blades and neck shards.
- Layered leather ribbons on both grip positions, with individual stitches;
  separate 2K color, normal, gloss and specular maps distinguish hide from iron.
- Small socket fasteners, halo rivets and surface-fitted cranial sutures.
  Tier 3 adds a pair of ritual forehead inlays.
- Uneven aged-bone pigmentation baked into the exclusive 2K skull atlas,
  retaining the anatomical cavities and existing normal detail.
- Separate chased-shaft and forged-blade materials from iteration 2. All 19
  image assets are resident, so first-person maps do not wait for streaming.

No animation or gameplay values change in this additional art pass. The staff
axis, grip centers and all four skull FX attachments remain fixed. View/world
vertex parity and existing casting grip/loop checks still apply.

Source LOD0 triangle counts: Tier 2 37,394; Tier 3 69,007. Each has two reduced
distance LODs. These counts and the resident textures are a real rendering cost;
no frame-rate claim is made without an in-game measurement.

Final native LOD0 counts are 37,394 and 65,928 respectively. The converter
discards microscopic Boolean bevel slivers on Tier 3: approximately 0.0053%
of its LOD0 surface area. `record_geometry.py` accounts for every removed
triangle from the actual converter diagnostics and bounds the lost surface area
below 0.02% in every LOD. No bone or leather geometry is lost. Leather rim UV
stretching warnings concern its thin edge faces and do not remove geometry.
Evidence: `art/necro_staff/compiled_geometry.json`.

## Reproduction and evidence

The actual Blender MCP studio runs `tools/necro_staff/detail_pass.py` against the
frozen iteration 2 source at `art/necro_staff/detail_pass/input.blend` and
`input_maps`. It writes only staged art while another native build is active.
Then run `detail_bone.py`, `detail_preview.py` and `detail_pose.py` through
`mcp_call.py`. The staging directory retains the editable model, exported native
LODs, texture inputs, render views and detail manifest.

`promote_detail.py` requires the preceding build to be audited or explicitly
marked interrupted, with no active game or native compiler. It archives iteration 2 evidence before promoting the exact
staged maps/models/GDT. Run the FULL guarded build afterward. Model/map changes
must not use the script-only path. Refresh `motion_preview.py` and
`motion_sequence.py`; `record_motion.py` rejects frames older than either current
model or animation metadata.

The macro review caught coplanar overlap between leather turns. `refine_grip.py`
applied a real seam to the already baked stage; `detail_pass.py` now generates
that spacing directly. Stitches sit on the outer hide surface. The dedicated
`detail_macros.py` views inspect bone, blade channels and grip seams.

The first native conversion exposed zero custom corner normals on a few valid
Boolean-cut blade triangles. The exporter now substitutes the geometric face
normal for those corners. The model gate checks every exported corner for a
finite unit normal; it was confirmed to reject the original offending binary.
Native rejection evidence: `tmp/necro_staff_build/native_zero_normal.log`.

`art/necro_staff/deployment.json` and `tmp/necro_staff_build/status.json` identify
the actual deployed revision. Source previews are not in-game screenshots.
The user judges native appearance, lighting and animation transitions; no agent
game launch is authorized.

Final build: September 27, 2026, FF written at 19:12:00 Eastern; full audit
completed at 19:13:51. FF 233,004,544 bytes; 449 source/deployment inputs matched;
both full sound banks 209,338,496 bytes. All 19 resident staff images, 34 staff
clips and tier/PaP models/materials are present. Soul Pulse's native blend/HDR64
material is verified. No runtime source was changed or synced after this build.
