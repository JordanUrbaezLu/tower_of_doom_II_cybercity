# Stronger red emergency sweep

## Newest: high-crown lamps get 4x emission

User requests much brighter red lamps on top of the crown because they are high
above the player, suggesting 4x intensity. The 16 point fixtures plus the apex
now select a dedicated ON model skin. Its red lamp emission is 144 (4 x 36).
The 13 hall lamps remain 36 and their spotlights are byte-for-byte unchanged.
The high variant reuses all three rotor meshes, texture images, LOD distances
and geometry, replacing only the emitting lamp material. Common OFF model,
1.5-second rotation, randomized starting angles and seal shutdown remain.

Blender MCP adds the high lamp material to the master and assigns separate
mesh-material slots to the 34 emitting parts across the 17 high fixtures.
This avoids changing the hall instances through shared mesh data. Matched
before/after distant-crown views are in `art/crown_alarm/high_crown_review`.
Blender bloom/bounce and final appearance are illustrative, not BO3 calibration.

PASS: actual runtime selection is 17 high / 13 hall; all go dark on seal;
duplicate calls and seal during startup remain safe; high skin changes only
emission and keeps all LOD/mesh settings; every preexisting GDT row and hall
FX matches the accepted private source. Writer is repeatable. Existing arity
and native API checks pass. ON log now also reports high_lamp=144.
The guarded compiled check requires the new model, its three LODs and material;
post-build audit checks both native emission values and the model skin override.
READY / NOT BUILT, waiting for Archer clearance in BUILD_HANDOFF.md. No launch.

## Latest: brightness accepted, random starting angles

User: the lights are too uniform and should have random starting points; then
"the brightness looks better now." Keep the existing intensity, reach, cone and
emission. Read-only audit confirms those sources match the private tools copy,
predate Archer's build-8 FF, the spotlight is packed, and native lamp emission is
36. Evidence: `art/crown_alarm/intensity_review/brightness_build8.json`.

New source change: each fixture draws `RandomFloat(360)` once on the server in
`init`, and adds it to the rotor yaw only. The base pitch/roll and housing remain
fixed, including the inverted pendant. All clients receive the same entity
orientation; no client-local random effect. Common activation and 1.5-second
revolution continue. No per-revolution reset, re-roll or delayed activation.
MOUNT logs include each phase; ON includes phase=random.

The existing harness now exercises actual init as well as start/stop: 30 draws,
30 fixed housings, retained inverted orientation, duplicate init/start preserving
phases, seal-during-start and dark shutdown. Script arity and 7816 API-site checks
pass. Blender MCP uses a reproducible illustrative seed for the refreshed matched
stills and motion; native game RNG remains per-match. Source READY, random phases
NOT BUILT. Archer's clearance is still required; no game launched.

## Previous intensity pass

User playtest, September 26: the current alarm lights feel weak, not threatening.
Target: a strong moving red wash across the hall, with a clearly luminous red
lamp behind the physical lens. The physical reflector remains the dominant
motion. All 30 lamps turn on together through the existing alarm trigger and
go dark at the crown seal; the 1.5-second rotation and siren timing stay intact.

The previous 360-unit, 62-degree horizontal cone cannot geometrically reach the
floor from a pillar lamp 244 units above it: the closest floor intersection is
about 474 units away. The pendant is higher still. This is a source geometry
finding, not a measurement of native shading or attenuation.

Candidate `red-sweep-2`: intensity 450 -> 1800; reach 360 -> 900 units;
cone 62 -> 78 degrees; lamp HDR 12 -> 36. Culling bounds and spawn-frustum
radius cover the new reach; viewer spawn range is 2400. Native RGB stays
exactly (1, 0, 0). The existing 13 shadowless hall spots remain the entire
dynamic-light budget; the 17 exterior lamps get brighter emission. One light
per fixture, 1000 ms interval / 1000 ms lifetime, no stacking or added sprites.

Blender MCP review uses the current crown geometry and matched before/after
camera, materials, exposure and fill. Blender spot power is an illustrative
conversion, not BO3 brightness calibration. It demonstrates sweep direction,
reach and relative contrast. Native brightness, performance and scary atmosphere
still require the user's playtest. No game is launched by this session.

Source status: READY, NOT BUILT. Geometry/image checks, the shipping lifecycle
tests, floor-reach/culling checks, 109-script arity and 7815 native API sites pass.
The old 360-unit cone fails the floor-reach negative control on all 13 mounts.
Matched stills and the 1.5-second sweep video are in `art/crown_alarm/intensity_review`.
The current master lamp was updated through Blender MCP; no mesh/texture rebake
was needed. The original source files are preserved in `intensity_before`.

Archived user log: `tmp/elite_tracking/runs/20260926_153852_841_a5eddc36/console_mp.log`.
It confirms ON fixtures=30, local_spots=13, turn_seconds=1.5. The next build's ON
log also records profile=red-sweep-2, reach=900, intensity=1800 and lamp=36.
This identifies the deployed tuning without per-frame logging.

Build request goes through the Archer lead in BUILD_HANDOFF.md; no build or sync
has run. Post-build `record_build.py` now also checks the native database lamp
intensity. Existing deployment/compiled-validation records are historical until
the coordinated build replaces them. Native appearance still needs user review.
