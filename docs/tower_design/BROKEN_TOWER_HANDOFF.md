# Broken tower descent — build handoff

2026-09-27 UPDATE: FULL build and script follow-up passed; final FF at 2026-09-27 10:45:04 -0400, 196,343,232 B; fresh LED 166,776,956 B. [Build evidence](BUILD_RESULT.md) and [receipt](build_receipt.json). The user retired Archer's lead role; all earlier clearance requirements below are historical and superseded. Current shared map: 10,624 world brushes, 584 lights, 24 drops, eight regular transit routes. Floor 40 is now the arena chamber. The user playtests; no game launch.

Follow-up: the [top transit bay](TRANSIT_HANDOFF.md) now accompanies this pass.
Use that handoff for current map counts and combined build status.

## Original source snapshot (historical)

2026-09-27. User requested a fixed irregular mix of doors and one-way drops on
the main 50-floor tower. No procedural randomness and no new teleporters.

Status: SOURCE READY. Request Archer clearance for a FULL build with fresh
BSP, navmesh and LED, including the preceding lighting/material pass. Clearance
has NOT been granted. No direct lead messaging tool is available; this handoff
is the coordination channel required by AGENTS.md. Record clearance in CLAUDE.md
before any build. Build 18 predates both passes. Do not ship via -GscOnly.

PRE-EDIT NOTICE (completed): this session owns tools/gen_tower_map.js and its
generated map/door data, _tod_doors.gsc (free drop zone activation and diagnostics),
geometry/navmesh lint extensions for explicit directed drops, relevant tests,
and CLAUDE.md top notes. Other class files, the spire and crown are outside scope.
Additional pre-edit notice: tools/build_map.ps1 will invoke test_broken_tower.js
beside the existing gameplay preflight gates. No build invocation is authorized
by that edit; clearance remains with Archer.
The preceding lighting/material pass is preserved and both passes are ready.

Implemented first pass: 24 selected lower stair flights collapse into 190-unit drops
with broad railed catch decks. Replace those floors' buy doors with broken
frames. Keep milestone-entry doors. Native zombie negotiation nodes use the
shipped Giant's zm_jump_down_190 pattern. Archer retains normal grapple access;
no invisible player ramp or class-specific teleport. Local landing protection
and dev diagnostics accompany the mandatory drops.

The main tower retains 26 paid stair-door transitions, including milestone
entries 11/21/31/41. Drops occur at laps 48,47,45,43,42,39,37,36,34,32,29,28,26,
24,23,19,18,16,14,13,9,7,6,3. Generated map: 10,579 world brushes, 2,709 entities,
582 lights, 38 generic paid-door rows. The detached spire's doors are separate.
Crown, causeway, terrace and spire brush bodies match the pre-break map exactly
after excluding generated GUIDs. No class ability or teleporter changes.

Validation passed:
- Emitted-map geometry lint: all 24 endpoints supported, crown-to-base route
  exists, every ordinary reverse route across a drop is blocked; baseline intact.
- Full geometry self-test: original holes/walls/severed-route controls, missing
  catch deck, restored return stair and alternate 49-floor parity all pass.
  Log: tmp/broken_tower/geometry_selftest.log (expected failures are test cases).
- test_broken_tower.js: fixed layout/data, deck coverage, shipping zone/fall
  helper behavior and navmesh section checker's negative controls. Now a build gate.
- GSC arity (112 scripts), native API (8,160 calls), Doppelghast (261 checks),
  crown hull/coverage, shared surfaces/provenance/conduits and tower light audit.
- The OLD deployed navmesh is correctly rejected as still connected across the
  new cuts. This is a stale-bake negative control, NOT a fresh navmesh pass.

Native status: unbuilt and unplayed. The new navmesh gate requires 25 connected
walking sections with mesh beneath all 24 directed traversal pairs. Do not waive
an unexpected seam or missing endpoint. It checks surfaces and authored links;
zombie animation playback/pursuit, ordinary jump/mantle, Archer grapple returns
and protected landings still need the user's native test after the FULL build.

Dev diagnostics: [TOD_DROP] INIT rev=1 upper=24 lower=24 fixed_layout=1,
APPROACH, ZONE_OPEN cost=0, LANDING_VOLUME and LANDING_PROTECTED; failure tags
MISSING_ROUTE / NO_ZONE_FLAG. Preserve active dev flags. Archive the user's
console_mp.log with tools/capture_ai_logs.ps1; never launch a match from this handoff.

Review: [actual-geometry preview](broken/review.html), [layout and behavior](BROKEN_TOWER.md).
No build, sync or game launch by this session. All builds remain with Archer.
