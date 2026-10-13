# September 27: whole-tower materials and power

The current pass covers both towers and their rooms: 1,109 floor/wall wire
inlays in 49 power-controlled regional models. Trial-hall liners now share
the crown kit too. [Current implementation and build status](TOWER_POWER.md)
and [matched off/on review](review.html) supersede the earlier 70-channel
scope and old lead-clearance notes below. The user retired lead clearance.
The FULL build and final script link passed; source/deployment and native
asset checks passed. No game launch; the user judges the native appearance.

---

# Color and powered wire details

User direction, September 26: restore the color and contrast lost when the
floor/wall kit migrated to detailed materials. Add subtle wires within the tower
surfaces that illuminate when power comes on; nothing excessive.

The comparison identifies the loss: blue floors and purple walls became neutral
gray, and gold structure became beige. Restore cobalt tread, violet service
panels, warm gold framing and distinct ruby/sapphire/emerald accents. Retain the
authored normal, gloss and wear maps and dark structural recesses.

The powered detail is a shallow service channel with recessed dark cables,
retaining clips, connectors and two fine cyan conductors. Place it sparingly at
floor junctions and in wall service panels. The unpowered model has no emission;
the powered twin lights only the narrow conductors. Use the existing power flag
and model swaps, with no new dynamic lights. Keep collision and navigation intact.

World material tints remain nonemissive. Model twins supply the switchable glow;
world brush material glow cannot be switched by the existing power flag.
All previews use matched geometry, camera, illumination and exposure. Blender
previews are authored-art evidence; the user verifies the native result.

Build coordination: request and status in ../crown_alarm/BUILD_HANDOFF.md. No
build or sync until the Archer lead records clearance. The user tests the game.

## Ready source and checks

Eighteen color roles are restored in `tools/art_cohesion/crown_materials.json`;
`install_surfaces.py` generates `source_data/tod_surface.gdt`. Both original
Blender tile libraries and their thirty baked maps are preserved. No exposure,
sky, world light, collision, route or prop finish was changed.

`12_author_conduit.py` authors the 22-part wire channel through Blender MCP.
It exports two rigid off/on models with three explicit LODs each (3272 / 610 /
346 triangles), twenty 512px image maps, and `tod_power_conduits.gdt`. A channel
is 96 by 18 units and 2.535 units deep. Only the two narrow cyan conductors emit:
on scale 3, off scale 0. The housing, cable insulation and clips do not glow.

`15_conduit_mounts.js` reads real emitted map solids and produces 70 supported
placements: one floor channel per tower lap, a wall channel every fifth lap,
four crown floor channels, four crown wall channels, and one in each side room.
It checks the transformed model footprint and outward normal against the real
support plane. No map regeneration or brush mutation. If geometry changes,
regenerate the placement data; the build gate rejects stale coordinates.

`_tod_power_conduits.gsc` initializes through the art-owned crown alarm module,
with a separate persistent `power_on` flag listener. The alarm trigger and seal
never turn the wires off. Server model state handles clients joining later.
The models are nonsolid. No polling loops, new lights, sounds or particle effects.
Automatic dev logs: `[TOD_CONDUIT] READY`, `ON`, `SPAWN_FAILED` with fixture ID,
kind and origin on failure. The crown alarm package contains the new scripts
and models; the existing surface sync already covers all native model inputs.

Checks passed: source texture hashes, native image bindings, six model binaries,
off/on geometry parity, supported/rotated placements, actual shipping init and
power-transition bodies (including duplicate init, already-powered init and
partial spawn failure), 109-script arity and 7,815 native API call sites. The
existing crown geometry, coverage and alarm tests also pass. The build's surface
gate runs the new checks; compiled alarm validation also requires all six native
conduit LODs. None of these establishes native visual/gameplay approval.

Preview sources and output are in `art/cybercity_materials/color_restoration/`:
`palette_change.json`, original palette/GDT/manifest snapshots, the two matched
crown .blend scenes and renders, `power_conduits.blend`, and the actual-placement
`powered_crown_review.blend`. The main review page includes the current map's
846 architectural pieces and all 30 red alarm fixtures. Hero/gameplay props,
runtime spotlights and sky are omitted; same camera/lighting/exposure on both
palette views. Original migration comparison remains in `migration_review.html`.

Build status: READY, not built or synced. Awaiting Archer lead clearance or the
user's explicit override, as recorded in `docs/crown_alarm/BUILD_HANDOFF.md`.
After one FULL guarded build, run:

```
python -B tools/art_cohesion/record_color_build.py --build-log <full-build-log>
```

That audit checks native material tints, compiled wire models/images/materials,
source/deployment hashes and absence of post-build sync. It writes a new
`color_restoration/deployment.json`; the earlier material-migration evidence stays
intact. No game launch. The user tests dark-to-powered glow, floor/wall seating,
color readability and their own preferred contrast; then archive console_mp.log.
