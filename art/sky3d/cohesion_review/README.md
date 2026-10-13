# Cybercity sky cohesion review

Open [the local gallery](index.html). These images are **Blender projection approximations; native BO3 playtesting is pending**. The separate [build receipt](build.json) records the compiled assets and source parity; these previews do not verify in-game appearance.

The pass replaces 363 ordinary window-box buildings with four distinct forms: 93 blade foundries, 95 split vaults, 93 transit bastions and 82 forked terraces. Their armor plates, asymmetric utility masses, open gaps and restrained light channels use the tall skyline’s architectural language. Existing lot and height bounds remain intact. The original tall spire geometry and generator random sequence are preserved.

The machined title monument and higher celestial composition share the darker cosmic setting. The skyline-clearance check covers all 20 celestial bodies, includes neon geometry and requires at least 3° separation.

| View | Current pass | Earlier view |
|---|---|---|
| Title reveal | [Final](final/cohesion_ingame_reveal.png) | [Same camera](before/sky3d_ingame_reveal.png) |
| City | [Final](final/cohesion_ingame_city.png) | [Same camera](before/sky3d_ingame_city.png) |
| Lower skyline | [Final](final/cohesion_ingame_down_l.png) | [Same camera](before/sky3d_ingame_down_l.png) |
| Giant planet | [Final](final/cohesion_ingame_giant.png) | — |
| Eastern celestial bodies | [Final](final/cohesion_ingame_celestial_east.png) | — |
| Upper sky | [Final](final/cohesion_ingame_up.png) | — |
| Cinematic reveal | [Presentation view](final/cohesion_ingame_reveal_cinematic.png) | — |
| Full equirectangular panorama | [Final](final/cohesion_sky_equirect.png) | — |

Only the first three rows are before/after comparisons. The cinematic reveal is a separate presentation view. The gallery links saved image files directly without grading, filters or image transformations. The final 8192 x 4096, 160-sample render took 508.158 seconds. The city score remains 0.64 and the whole-sky score is 0.6456634402275085; [finish measurements](final/cohesion_stats.json), [title bounds](title.json) and [celestial clearance](clearance.json) retain the measured evidence.

- [Finished HDR Blender preview](../sky_preview.blend), saved with Rendered shading and Scene World enabled; Numpad 0 restores the title camera. [Viewport screenshot](blender_preview.png) and [settings](preview.json).
- [Canonical Blender master](../tod2_sky.blend)
- [Build receipt](build.json); this is separate from the visual review and does not replace native playtesting.

The three `before/` files are unchanged copies of the corresponding `docs/sky_preview/sky3d_ingame_*.png` views captured before this pass.

The guarded FULL build completed at 19:45:13 Eastern on 2026-09-29 with a fresh lighting bake and compiled sky image. The receipt proves all linked inputs and 17 authoring artifacts; 208 runtime files match the snapshot exactly. One copied `_tod_lucky.gsc` changed during a peer's work but is absent from the compiled ledger and unreferenced by packed sources. That file is recorded explicitly; whole-snapshot parity is not claimed. Native appearance remains unplayed.
