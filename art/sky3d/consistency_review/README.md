# Reviewed and built skyline consistency pass

The [comparison gallery](review.html) shows the approved layout and the revised
city/celestial surfaces. All 1,189 ordinary buildings share the close cyber kit;
the large landmarks and title frame share its worn graphite/alloy treatment.
Planet and star emission is reduced locally, with the approved finishing gain
held fixed. The station, reduced layout and measured celestial clearance remain.

The shipping panorama has the dull pre-jump title. The native card illuminates
it after the reveal. Its derived Blender material bake preserves foreground
coverage and separates reflected frame/spill from bright lettering and tubes.
See [Before jump](blender_before_jump.png) and [After reveal](blender_after_reveal.png).
These are approximate Blender previews, not BO3 screenshots.

Guarded FULL BUILD OK 2026-09-30 11:26. [Build proof](build.json) records 212
matching runtime inputs, 111 authoring artifacts, fresh map/sky/probe lighting,
and the packed sign model/material/image. Current source parity passes. Final
native appearance and reveal behavior remain the user's playtest; no game was
launched.

[Reproduction](../../../tools/sky_consistency/README.md) and
[integration details](INTEGRATION.md) describe the source contracts. Earlier
failed GDT-header and texture-mipmap attempts are retained as
`failed_gdt_build_inputs.json` / `failed_mips_build_inputs.json`; their logs are
under `tmp/sky_consistency/`. `pre_sqlite_verifier_build_inputs.json` preserves
the verifier-only capture superseded before the successful bake and link.

Open [the preview launcher](../../../tools/sky_consistency/open_preview.ps1)
to restore Rendered mode, Scene World and Scene Lights. The Scene selector
switches Before jump / After reveal. The saved preview is kept byte-identical
to its build snapshot when reopened.
