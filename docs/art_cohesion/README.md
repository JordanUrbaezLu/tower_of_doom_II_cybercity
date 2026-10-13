# September 27: whole-tower materials and power

The current pass covers both towers and their rooms: 1,109 floor/wall wire
inlays in 49 power-controlled regional models. Trial-hall liners now share
the crown kit too. [Current implementation and build status](TOWER_POWER.md)
and [matched off/on review](review.html) supersede the earlier 70-channel
scope and old lead-clearance notes below. The user retired lead clearance.
The FULL build and final script link passed; source/deployment and native
asset checks passed. No game launch; the user judges the native appearance.

---

# Current color restoration and powered wires

September 26: the user requested the earlier palette back and subtle power-on
wire details. See [current review](review.html) and [implementation/status](COLOR_RESTORATION.md).
The richer palette supersedes the muted-color direction below. Source work is
ready; the full build awaits lead clearance. The September 25 migration record
below is retained as history.

ï»¿# Realistic materials for the complete crown

September 25, 2026. The user chose a more realistic Tower of Doom II, using the
detailed shop, teleporter and sky as the reference. They then expanded the work
to **the entire crown section**, specifically rejecting a partial test bay.
The current implementation covers the whole detached crown island. The rest
of the tower retains its current materials until that next phase is requested.

## What changed

- All 803 visible architectural solids, 8,634 world faces, and the six faces of
  the crown gate use the new material family. Coverage includes the hall,
  sanctuary, exterior shell, swept underside, points, arches, decorative
  pendants, jewels, approach, balcony, passage and overlook.
- Dark steel, aged brass, subdued ceramic and colored glass replace the old
  flat grid/blackout-clone surfaces. Larger exterior panels reduce the small,
  repeated-block appearance at the tower viewing distance. Tread and service
  panel detail remain finer at player distance.
- The entire existing floor and west wall are whole solids again. Architecture,
  collision, routes, shop anchors and gameplay are preserved. The original
  crown stays open above; no new room ceiling was added.
- The detailed shop designs stay intact. Teleporter ready/off and Heavenly
  Altar finishes have been softened as described below. Original portal art,
  pink ready/yellow recharge/dark off states and shop animation/audio remain.
  Stock perk machines, ammo crate and power lever retain their native models.

The new world materials have **zero emission**, respecting the user's concurrent
blackout/power-wave direction. The native powered lights reveal their surfaces;
this pass does not add permanent architectural glow or change the lighting rig.
Device glow remains controlled by its existing state logic.

## Authored sources and reuse

`art/cybercity_materials/cybercity_material_library.blend` holds four physical
128-unit tile sources and eight reusable source materials. The floor has tread
plates, captive fasteners and local scuffs; the wall has service cassettes,
ventilation, seals and protected guide channels. Ceiling ventilation and a
four-strip trim sheet support later enclosed spaces.

`crown_surface_library.blend` adds interlocking armor panels and frosted crystal
inserts, plus three source materials. Both libraries were authored through
Blender MCP. The shared kit now supplies thirty 1024px maps: base color, DirectX
normal, fullspec, relative gloss and emission for each of six tile sources.
Native world emission is deliberately disabled. The map uses five tiles; the
ceiling sample is saved for future interiors.

`tools/art_cohesion/crown_materials.json` defines twenty native material roles,
including the eighteen used on this crown. Interior floor/wall/trim repeat every
128 native units. Main exterior armor repeats every 512 units; crystal surfaces
use 256. Native palette/finish definitions come from `surface_definition.py`;
shared prop profiles come from `profiles.py`. Color roles retain recognizable
crown metal, dark structural recesses and ruby/sapphire/emerald accents, with
lower saturation than the inherited materials.

New Blender assets should reuse this material library and its panel/joint,
fastener, bevel and wear conventions. Hero props may retain their unique atlases.
Do not stretch a prop atlas over architecture or rely on a studio render as a
native material approval.

## The excess-gloss investigation

The source/database audit confirmed these original native settings:

| Surface | Normal map | Gloss maximum before | Current candidate |
|---|---|---:|---:|
| Accepted shop body | Baked | 8 | 8, unchanged |
| Teleporter ready/off body | Baked | 13 | 8 |
| Heavenly Altar body | Baked | 6 | 5 |
| New architecture | Baked | â€” | 5â€“9, according to finish |

The teleporter's specular amount/tint and probe amount now match the accepted
shop profile. The altar retains its previously accepted nonzero highlights;
only its gloss ceiling is reduced. No all-matte flattening or geometry changes.
UV-face-centroid samples of the gloss maps gave medians .596 for the teleporter,
.733 for the altar and .451 for the shop. Those are samples, not an area-weighted
brightness measurement. `finish_before.json` and `finish_changes.json` record
the exact native changes. `tmp/art_cohesion/finish_audit_*.json` records the audit.

The teleporter preview previously assumed metallic .7 and used `1-gloss`
without the native gloss range. The altar preview imposed metallic .15,
specular .2 and a roughness remap of .65â€“.9. These settings made the Blender
preview a poor predictor of the exported result.

`native_preview.py` now uses exported maps, actual native gloss ranges, and
sRGB-to-linear material tints (as the installed color/specular techsetdefs do).
Its fullspec/GGX shading and exponent-to-roughness conversion are explicitly
**approximations**. It does not reproduce BO3's BRDF, probes, exposure, lighting
states or tone mapping. The reduced native gloss is a candidate fix that still
requires the user's visual test; lighting may also affect the appearance.

## Review files

[review.html](review.html) now opens with a matched before/after comparison:
before on the left, after on the right, with synchronized hall, tower-side,
exterior and underside buttons. Each pair also has a standalone
`crown_<view>_side_by_side.png` export.

The before view is reconstructed from `crown_before_refactor.json` and the
unchanged `tod_black_*` material definitions, including the user's blackout
pass. The initial test bay's floor and west wall are restored to their original
material families across the whole solids. Prop finishes use `finish_before.json`.
Geometry, review lights, exposure and cameras are identical; these are Blender
material comparisons, not screenshots of a prior game build. The finished
`crown_complete.blend` is unchanged. `before_after_manifest.json` records source
and image hashes, matched cameras and the two whole-solid material restorations.

Reproduce with Blender `10_render_before.py`; both render scripts share
`crown_views.py`. `11_export_comparisons.js` captures the HTML layout through an
owned headless Chrome session on port 9339 and checks all four view buttons.
No map rebuild is needed for this preview-only comparison.

[review.html](review.html) presents the complete crown: exterior, tower-facing
view, hall and underside. `crown_complete.blend` contains the actual generated
convex solids and the preserved shop, teleporter and altar meshes at their map
anchors. Studio lighting makes the surfaces readable; these are not BO3
screenshots. Stock perk/lever/crate props and runtime FX are omitted from the
architecture render, but remain in the map. The altar portal shows only its
original first layer. Brush texture projection in Blender is an axial preview.

The older `native_comparison.blend` and ready/off/recharge renders are retained
as initial common-rig studies. They predate the full-crown palette/blackout pass
and should not be treated as the final crown preview.

## Reproduction and native checks

1. Author the base kit through MCP with `01_author_kit.py`; bake with Blender
   `02_bake_kit.py`. For the crown extension, run `06a_open_library.py` and
   `06_author_crown.py` as separate MCP calls, then bake `07_bake_crown.py`.
2. Run `install_surfaces.py`, then `node tools/gen_tower_map.js`. The generator's
   scoped `crown_surfaces.js` pass remaps world and entity brush faces only on
   the detached crown. It includes the low-hanging ornaments and the gate.
3. Run `verify_surfaces.py`, `verify_geometry.js` and `verify_crown.js`. These
   are also guarded-build gates. The coverage audit reads actual emitted
   planes, rejects leftover old materials, and compares the complete crown's
   shape to the recorded pre-refactor geometry. Ordinary geometry/navigation
   gates still run. There are no new gameplay changes requiring new logs;
   existing device/state diagnostics remain enabled.
4. Assemble `08_crown_scene.py` through MCP and render `09_render_crown.py`.
   Original shop/teleporter/altar masters are untouched.
5. Snapshot `verify_deployment.py --snapshot` immediately before a FULL guarded
   `tools/build_map.ps1` run. Run the verifier afterward to prove deployed
   source hashes, packed world materials/images and native database settings.
   Never sync over an active peer build or user match.

The FULL guarded build passed on September 25, 2026. The fresh fastfile is
206,925,056 bytes, written at 11:20:25 local time. Deployment verification
matched all 403 captured source inputs, eighteen packed crown world materials,
twenty-five used surface images and all twenty-three native finish definitions.
Compiled shop, teleporter, altar and partner asset checks also passed. The
linker reported only its eight existing, explicitly waived asset warnings.

A separate sky session changed the sky EXR at 11:21:56, after this fastfile
was packed, and started its own FULL build at 11:23:13. The crown inputs are
unchanged. The strict verifier correctly rejects comparing that newer source
tree to our earlier snapshot; no check was waived or snapshot overwritten.
`deployment.json` records our completed crown verification, while
`post_build_source_changes.json` records the subsequent sky change. Wait for
the sky session's build verdict before playing; its build log is
`tmp/sky3d_build/full_build_v6_112313.log`.

The user tests; no game launch by the agent. Native appearance is pending.
Inspect the crown from the tower after jumping across, plus its hall and
balcony at player height, then compare the teleporter and altar finishes under
powered lighting. Build result: see `art/cybercity_materials/deployment.json`.
