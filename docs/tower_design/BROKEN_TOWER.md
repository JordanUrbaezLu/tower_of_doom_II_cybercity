# Broken descent — fixed layout

The main tower now mixes 26 intact stair-door transitions with 24 collapsed
transitions. This is an authored layout, identical on every generation and match.
The crown, detached spire, milestone-entry doors and existing teleporters remain
as before. No new teleporters are part of this pass.

Each selected floor keeps its upper stair flight. Its lower flight is missing:
the midpoint landing becomes a ledge, with a 190-unit drop onto a 160 x 512-unit
railed catch deck. The deck reconnects to the preceding floor at the old doorway.
The buyable slab, anti-bypass door clip, intact frame and stair ramp are removed.
Uneven frame stumps and hanging edge fragments mark the break. There is no hidden
player ramp. Archer's grapple is unchanged and can target the retained upper
walkable landing; the actual grapple return needs the user test.

Descending drop floors: **48, 47, 45, 43, 42, 39, 37, 36, 34, 32, 29, 28, 26,
24, 23, 19, 18, 16, 14, 13, 9, 7, 6, 3.** Other main-tower floor transitions keep
their paid door. Floors 11/21/31/41 retain the existing enemy milestone gates.
Consecutive drops are separate landings, not a single fall spanning two floors.

Approaching a drop opens its existing next-floor zone flag at no cost. A lower
catch-volume trigger provides a second activation path. This avoids entering an
inactive zone, retaining normal spawning and playable-area behavior. Existing
force-open callers also recognize the missing gates. No points or door-purchase
rewards are granted by a drop.

Mandatory drop landings receive localized fall protection: MOD_FALLING only,
within 2.5 seconds of touching that drop's upper approach, on its own catch floor.
It is consumed on the landing damage callback. This does not grant a class-wide
fall-damage immunity or change damage elsewhere.

Each break has a directed native zombie negotiation pair using
`zm_jump_down_190`, matching the shipped Giant nodes' 51-unit forward / 190-unit
down displacement. End nodes do not link back. The compiled-navmesh gate now
requires one connected walking section between every pair of authored cuts,
mesh under both ends of each drop, and a directed route down all sections. It
still rejects accidental islands and stairs bridging the intended breaks.
This verifies mesh surfaces and source links; animation playback and pursuit
across them require the full native build and user test.

The geometry gate samples the emitted map, permits only the explicit drop
mouths with supported floors below, and checks every drop's reverse route
individually. Its baseline remains unchanged. Negative controls remove a catch
deck and add a return stair, in addition to the existing holes/walls/route/parity
tests. The old compiled map is correctly rejected against this new layout.

Relevant source: tools/broken_tower_layout.js, tools/gen_tower_map.js,
_tod_doors.gsc, generated _tod_door_data.gsc. `test_broken_tower.js` exercises
the emitted geometry, generated/runtime data, shipping landing and zone helpers,
and navmesh validator failure cases. It runs in the build preflight.

Dev logs run automatically: `[TOD_DROP] INIT`, `APPROACH`, `ZONE_OPEN`,
`LANDING_VOLUME`, `LANDING_PROTECTED`; failures include `MISSING_ROUTE` and
`NO_ZONE_FLAG`. Landing-volume entry is not itself a grounded-contact assertion.
After the user's test, archive console_mp.log with tools/capture_ai_logs.ps1 and
inspect these tags alongside `[TOD_ARCHER]` and the normal AI diagnostics.

Native status: FULL build, fresh lighting and compiled navigation checks passed.
[Build evidence](BUILD_RESULT.md). No game launch by this session. For the user test:
try a door/drop pair, consecutive doors, consecutive drops, ordinary jump/mantle
back up, Archer's grapple return, zombie pursuit, and landing damage with god
mode off. Do not change the user's active dev flags as part of this source pass.

[Visual review](broken/review.html) · [Build handoff](BROKEN_TOWER_HANDOFF.md)
