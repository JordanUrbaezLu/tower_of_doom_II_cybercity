# Whole-tower surfaces and powered inlays

September 27, 2026. The user reiterated that the entire tower needs the crown
material family and visible material details that turn on with power.

The earlier conversion missed seven trial-hall wall liner materials. These now
use the crown's panel/trim kit in their existing district colors. The custom
crest plaques and floor trial-mark signs remain. The source audit enumerates
every material and permits only the crown kit, these signs and utility surfaces.
All architectural colors retain baked normals, gloss and wear.

The previous power detail consisted of only 70 small channels, with no spire
coverage. The new layout uses 1,109 shallow channels, supported by actual brush
planes: four floor channels and four inward/outward parapet channels per lap,
plus room details in the base, four breathers, seven trial halls, top transit,
crown and side rooms, summit and arena. Every main-tower and spire lap is covered.
The original authored channel is lengthened to 134.4 units without thickening
the housing. Fine conductors use emission 8 (previously 3); housing emission is
zero. The existing 584-light rig illuminates the textured architecture.

There are 49 server hosts, down from 70. Nearby channels are merged by material
into regional models, with two native LODs based on the original authored medium
mesh: 610 triangles per channel nearby, 436 at distance with the retaining clips
omitted. The original 346-triangle distant mesh lost triangles during native
conversion when batched; the replacement retains the validated shell and wire
geometry. The compiled check requires exact triangle counts. Collision is disabled.
Persistent `power_on` chooses the
correct twin at initialization and at the power transition. Server model state
replicates to late joiners. The opening alarm stopping cannot extinguish them.

Regenerate with `node tools/art_cohesion/15_conduit_mounts.js` after geometry
changes, then `python -B tools/art_cohesion/build_conduit_batches.py` when the
mounts change. The gate rejects stale transforms, source meshes or native LODs.
No geometry or navigation changes are made by this system.

Source checks exercise off/on, already-powered init, duplicate init, and a failed
regional spawn without shifting the remaining model assignments. Native source
and compiled-asset checks verify all twins, LODs, materials and deployment.
Dev logs automatically report expected/live hosts and visible-channel counts;
failed spawns name the affected region. Expected healthy output is
`READY revision=tower_wide_v2 hosts=49 expected=49 channels=1109` and
`ON hosts=49 channels=1109 reason=power_on`.

Status: FULL build plus final script-only follow-up verified at 2026-09-27 12:01:18 Eastern.
Logs: `tmp/tower_power_build/full4.log` and `full4d.log`. The full bake is fresh;
its BSP/navmesh/LED are hash-identical after the follow-up. All 654 captured
inputs match deployment; scripts, UI and zone trees match with no later sync.
All 100 wire models / 202 LODs retain their expected native geometry. All 29
used architectural material roles are in the packed ledger. FF 193,176,704
bytes; sound bank 209,338,496 bytes (199.6 MB), matching the good full build
after the known audio-checksum retry. [Build receipt](tower_power_build_receipt.json).
No game launch. Native appearance, brightness, distance readability and
performance await the user's playtest.
