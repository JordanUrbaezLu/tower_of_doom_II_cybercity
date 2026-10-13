# September 27: high crown alarms visible from below

**Build status (2026-09-27 15:07:59 Eastern): full build and exact-source deployment passed.** Includes the balcony, crown lights, Necromancer, Fire Bow, C4 and Warrior fixes. Fresh BSP/navmesh/lighting; FF 193,919,232 bytes; 378 captured inputs matched. Evidence: `tmp/crown_alarm_visibility/full_build.log` and `art/crown_alarm/deployment.json`. This supersedes earlier queue/relink notes below. Native visuals and gameplay await the user's playtest; the agent did not launch the game.

User screenshot: `Screenshot 2026-09-27 135723.png`. Request: bigger and much
brighter red alarms on the high crown arms, deliberately exaggerated.

The captured user run confirms the previous high emission 144 was active:
`tmp/elite_tracking/runs/20260927_140026_154_e2d08d60/console_mp.log`, ON at
54950 ms. That implementation attached real lights only to 13 hall fixtures;
the 17 points/apex had emissive surfaces only.

This pass doubles the high fixtures' upper housing, lens and rotor, retains the
original bolted mounting foot, and raises their emission 144 -> 576. The rotor
pivot rises from 26 to 48 local units to match the new housing. Off and on use
the same enlarged geometry. The hall fixtures and their sweep FX stay unchanged.
Each high fixture now gets a shadowless red omni: intensity 14400, radius 2400,
spawn distance 20000, bounds 2600. It lights the upper arms independently of the
reflector's direction; the visible reflector still rotates every 1.5 seconds
with the same random initial phase. This is a deliberate strong first retune;
native brightness, draw distance and cost remain the user's playtest.

No new server hosts, clientfield bits, textures, shadows or gameplay timers.
Thirty bounded FX lights at most (13 hall + 17 high), one particle per effect:
1000 ms lifetime and interval. Same alarm start and crown-seal shutdown.
`[TOD_CROWN_ALARM] ON revision=high_visibility_1` logs the high light count,
size, reach, intensity and emission. Initialization, repeated start/stop and
seal-during-replication checks exercise the actual GSC bodies.

Blender MCP authoring: `tools/crown_alarm/10_high_visibility.py`, evidence in
`tmp/crown_alarm_mcp/20260927_140239_870897.json`. Editable derivative:
`art/crown_alarm/visibility_review/high_fixture.blend`. The existing master
and nine original native meshes remain intact; six new LOD files retain the
original triangle counts, UVs and weights. `04_tune_light.py` owns native
materials, model variants and both FX definitions.

Matched upward-looking [before](../../art/crown_alarm/visibility_review/before.png)
and [after](../../art/crown_alarm/visibility_review/after.png) were assembled and
rendered through Blender MCP by `11_visibility_review.py`. These illustrate
geometry and relative emission; Blender light energy/bloom is not BO3 calibration.

Source/state/API gates pass. Full build is queued by
`tools/crown_alarm/build_when_idle.ps1`; it waits for the user's running game,
runs the guarded full build, checks source hashes and deployment, and stops.
Current machine-readable status: `tmp/crown_alarm_visibility/status.json`.
Build log: `tmp/crown_alarm_visibility/full_build.log`; successful deployment
receipt: `art/crown_alarm/deployment.json`. Do not infer success from the queue.
No game launch by this session.
