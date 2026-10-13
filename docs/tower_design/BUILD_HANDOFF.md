# Tower lighting and materials — build handoff

2026-09-27 UPDATE: FULL build and script follow-up passed; final FF at 2026-09-27 10:45:04 -0400, 196,343,232 B; fresh LED 166,776,956 B. [Build evidence](BUILD_RESULT.md) and [receipt](build_receipt.json). The user retired Archer's lead role; all earlier clearance requirements below are historical and superseded. Current shared map: 10,624 world brushes, 584 lights, 24 drops, eight regular transit routes. Floor 40 is now the arena chamber. The user playtests; no game launch.

Latest follow-up: [top transit bay and crown return](TRANSIT_HANDOFF.md).
Its handoff carries the current combined map counts and build status.

## Original source snapshots (historical)

2026-09-27 FOLLOW-UP: user requested broken descending floors. The lighting
pass and the subsequent [broken tower pass](BROKEN_TOWER_HANDOFF.md) are both
SOURCE READY. Build them together with fresh BSP/navmesh/LED. Clearance remains
pending. Counts below describe the earlier lighting-only snapshot; the combined
map now has 10,579 world brushes and still has 582 lights.

2026-09-27: User requested a brighter visible sky, lighting throughout the map,
and tower textures matching the crown. This session owns that source pass.

Pre-edit notice to Archer lead: planned shared edits are `tools/gen_tower_map.js`
and its generated map/data, `source_data/tod_skybox.gdt` plus sky asset finishing,
and extensions to `tools/art_cohesion/` / its generated surface GDT. Any necessary
lint integration will be identified before editing it. No class/gameplay edits.
Preserve the current alarm/power transition, crown art, geometry and anchors.

Status: SOURCE READY. Request Archer clearance for the next FULL build with a
fresh lighting bake. No sync, build or game launch has run in this session.
No direct lead messaging tool is available; this document is the coordination
channel required by AGENTS.md. Clearance has NOT been granted. Please record
the build clearance in CLAUDE.md's top note. Build 18 predates these map changes.

Pre-edit notice: adding a concise source-readiness / pending-build pointer to
CLAUDE.md's top notes now. No build script, lint tool, class or gameplay edit.

Ready source:
- Generated map: 11,083 unchanged world solids; 240 new stair lights; 293 existing
  lights retuned; 582 total lights. All new lights use powered state only.
- Crown material family on 53,394 additional faces, 11 additional tint roles,
  the same 30 baked texture maps. Crown material assignments remain intact.
- Same 8192 x 4096 v6 sky, score 0.32 -> 0.64; saturation remains 1.2.
  skyStops 1.85 -> 0.85 compensates the doubled image energy in the world bake.
- No new zone lines: brush materials are implicit map dependencies. Surface GDT
  and sky EXR/GDT must accompany the map. Do not ship via -GscOnly.

Checks passed:
- Whole-map geometry lint; emitted crown convex-hull test; crown coverage and
  material-bay geometry validation; shared surface/provenance and conduit gates.
- Doppelghast preflight: 261 checks, including alarm/calm/siren contracts.
- verify_tower_design.js against tmp/tower_design/before/map_source/zm/zm_tod2_cybercity.map:
  every brush plane identical, non-light entity content identical except materials,
  prior light origins/state flags unchanged, zero new light origins in solids,
  no old architecture materials, calculated sky bake-energy ratio 1.00000054.

Review: [source and tuning notes](README.md), [visual review](review.html),
[machine-readable source audit](source_validation.json).
Native light limits, performance, reflected appearance and final brightness still
require the FULL build and user playtest. Preserve the existing armed dev flags.
Use existing [TOD_LIGHTSTATE], [TOD_FALL], [TOD_CONDUIT] logs after the user's run;
archive with tools/capture_ai_logs.ps1. Never launch a match from this handoff.
