# Top-floor transit bay — build handoff

2026-09-27 UPDATE: FULL build and script follow-up passed; final FF at 2026-09-27 10:45:04 -0400, 196,343,232 B; fresh LED 166,776,956 B. [Build evidence](BUILD_RESULT.md) and [receipt](build_receipt.json). The user retired Archer's lead role; all earlier clearance requirements below are historical and superseded. Current shared map: 10,624 world brushes, 584 lights, 24 drops, eight regular transit routes. Floor 40 is now the arena chamber. The user playtests; no game launch.

2026-09-27 10:29 BATTLE ARENA: floor 40's pair is removed (the floor-40 spur is the arena chamber, docs/185); the network is now 8 routes (top bay <-> 30/20/10, base <-> crown). The combined FULL build carries it. NOTE for this build's deployed=repo check: `_tod_arena.gsc` was edited AFTER full3's sync (a stuck-straggler watchdog, script-only) - that one diff is expected and rides a -GscOnly after this build.

## Original source snapshot (historical)

2026-09-27. SOURCE READY. User requested the four-floor teleporter
bay at the main tower's top landing (40/30/20/10, two-way), removal of the old
bottom bay, and one bottom pad linked to the crown's right-hand teleporter.

Pre-edit notice: this session owns tools/gen_tower_map.js and generated map /
crown data / door data / breather data, _tod_teleport.gsc, the obsolete tpbay zone adjacency in
zm_tod2_cybercity.gsc, and the crown-return integration in _tod_fall.gsc. Relevant
geometry/navmesh and teleport test gates, preview tools, build preflight and
CLAUDE.md top notes may be updated. Preserve all class and peer art edits.
Additional notice: the sealed-island spawn filters in _tod_endless_rounds.gsc
and _tod_doppelghast.gsc must recognize the crown return opening, so the restored
crown cannot become an enemy-free refuge. Only those conditions are in scope.

The new room joins the top terrace beside the jump-pad landing, uses the crown
material family, and contains four floor pads. Destinations unlock when reached
during descent. Floor pads return to this top room. The bottom gets a compact
open landing with one crown pad; the old enclosed four-pad bay is removed.
Returning from the bottom restores crown service access after the opening seal.
Existing pad art, charge/cooldown, power rules and sounds are reused.

Includes the preceding lighting/material and broken-descent passes. No sync,
build or game launch by this session. ALL builds await Archer clearance recorded
in CLAUDE.md, per AGENTS.md. No direct tool can message that separate lead;
this handoff is the required coordination channel. FULL BSP/navmesh/LED needed.

Request the next FULL build including all three map-design passes. Clearance
has NOT been granted. Build 18 predates all three; never ship these via -GscOnly.

Current source: 10,615 world brushes, 2,731 entities, 580 lights, 37 generic
door rows. Main descent still 24 drops / 26 paid transitions. Transit has ten
physical source pads: four top-room pads, four floor-return pads, one base pad
and one crown pad. Existing independent spire transport is unchanged.

Changes beyond the room:
- Generated route rows/markers own every source, destination and unlock flag.
  Top destinations use descending entry gates 41/31/21/11; crown-to-base uses
  enter_lap1. The old bottom room/door/tpbay_zone adjacency is removed.
- Occupied base returns open the crown side-room door and reopen the main hall,
  restore its spawns/respawns, and stop the sealed-island filters. The alarm
  phase remains finished. Empty charges do not reopen anything.
- Co-op floor-arrival offset grows 160 -> 208, with generated gantry risers
  following it. This keeps the full 48-unit arrival ring outside departure gather.
- No new zone assets or device-art changes. Crown kit texture sizes are applied
  explicitly to the new room; four powered light pools and a fitted room probe.

Checks passed: emitted-layout/runtime transit harness (including missing flag,
disabled zone, failed return, idempotent crown reopening, restored spawning and
respawns); whole-map geometry; mirrored 49-floor parity; broken-drop test;
jump-pad arc; hoop; arity (112 scripts) / native API (8,185 call sites);
teleporter FX; Doppelghast (261); crown preservation; material/conduit audit.
Evidence: tmp/transit_bay/source_checks.log, geometry.log, parity.log.
The build preflight now runs test_tower_transit.js. The compiled-navmesh gate
checks all ten pads and each arrival fan-out against its area's walking component.
No fresh compiled navmesh exists yet; do not waive missing/isolated pad mesh.

Automatic diagnostics: [TOD_TELEPORT] INIT rev=2 routes=10, ROUTE, STATE,
CHARGE, DENY, FIRE, ARRIVE, PAD_FAILED; [TOD_FALL] RETURN_OPEN. Preserve existing
dev flags. User test: each pair both ways, normal destination locks, four-player
and downed ride-along, cooldown, crown gate access and enemy pressure after return.
Archive console_mp.log with tools/capture_ai_logs.ps1. No agent-run match.

[Source notes](TRANSIT.md) · [actual-geometry / native-pad review](transit/review.html).
Previews are Blender studio renders; runtime travel and final lighting are unplayed.
