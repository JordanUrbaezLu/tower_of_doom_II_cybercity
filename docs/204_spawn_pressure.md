# 204 — Spawn pressure: THE AMBUSH + THE TRICKLE

**Status: BUILT 2026-10-03: -GscOnly BUILD OK 04:43 (tmp/ambush/gsc1.log): .ff 04:43:00, FF 229,081,856 B; AMBUSH OK ran inside it; the ledger carries scriptparsetree _tod_ambush.gsc + _tod_endless_rounds.gsc; scripts / zone_source / ui deployed = repo, nothing synced after the .ff, no repo source edited after the build start; the 8 known-waived linker lines only. UNPLAYED.** The user judges the feel in a playtest; the
dev log `[TOD_AMBUSH]` records every decision (section 6).

User, 2026-10-03: *"This map should be more hectic than the first. Whats the max zombies at
once?"*, then *"Lets check spawns and spawn rate speed and things as well. We should have
challenging spawn points as well to make it tougher."*

## 1. The audit: what this map did, against the first map

Everything about WHERE and HOW FAST ordinary zombies arrive was copied from Tower of Doom 1
unchanged. Only the live cap was higher.

| | Tower of Doom 1 | Tower of Doom II before | Tower of Doom II now |
|---|---|---|---|
| Live cap (1 / 2 / 3 / 4 players) | 30 / 35 / 40 / 45 | 36 / 42 / 48 / 54 | unchanged |
| Spawn delay | stock x 0.83 | stock x 0.83 | stock x **0.70** |
| Spawn floor | 0.25 s | 0.25 s | **0.20 s** |
| Rampage | x 0.80, floor 0.20 s | same | x 0.80, floor **0.16 s** |
| Round size (stock 24 + 6 a player) | 24 / 6 | 24 / 6 | **28 / 7** |
| Movement speed curve | sprint gait from round 1 at 0.8, full at round 18 | same | unchanged |
| Spawn points | 2 fixed risers per floor, on the landing corners | same | the corners **plus THE AMBUSH** |
| Spawn pick | random among the risers of the active zones | same, after the reach filter (docs/200) | **a share climbs out round a player** |

The live cap, the actor ceiling (60, minus allied actors) and the elite roof are not raised:
the live cap is already 20% over map 1 and the engine ceiling is close.

Two facts drove the design:

- **The authored spawn points are predictable.** Every ordinary floor has exactly two risers,
  one on each landing corner (`tools/gen_tower_map.js`), and stock chose one at random from the
  floor you stand on and the floors above and below. Six fixed corners, the same on all fifty
  floors. A player learns them in two floors, holds a landing facing the stairs, and the
  trickle arrives in a queue from known directions. A third of it rose a floor away.
- **Under THE TWIST a round lasts (round size x spawn delay).** A faster trickle alone shortens
  every round and races the round counter, which drives the health curve, the card deals and the
  elite unlocks. So the rate and the round size move together.

## 2. THE AMBUSH: challenging spawn points

`scripts/zm/zm_tod2_cybercity/_tod_ambush.gsc`, called from the spawn hook
(`_tod_endless_rounds::finale_spawn_selection`) outside the parked finale's aggro run.

**The share.** 30% of ordinary spawns on round 1, rising linearly to 60% by round 15, +15 while
the Rampage inducer is on, never over 80. The other spawns keep the authored corners, so the
generator's hall, base and wing layouts still matter.

**The direction**, rolled per spawn, round one random upright player (the focus):

| Direction | Share | Where |
|---|---|---|
| AHEAD | 50% | Within 60 degrees of where the focus faces: the stairs they are heading down, the landing they run at. It may be on screen; a zombie clawing out of the floor in front of you is the point. |
| BEHIND | 35% | More than about 105 degrees from the view AND off every player's screen: the floor just left, the flight above. The camping counter. |
| FLANK | 15% | Anything else in the ring. |

The asked direction is tried first, then a flank, then the opposite one, then the corners. The
spot is a ring of navmesh points 360 to 900 units round the focus, one flight up or down
(`PositionQuery_Source_Navigation`, cached 0.5 s a player). The zombie arrives through stock's
own climb-out (the riser animation, the dirt, the sound): the spot is a riser struct, the same
shape as THE HUNT's navmesh arrivals.

**The rules it never breaks.** Each is a filter the hook already applied to the corners,
re-applied to the synthesized point:

- the point can WALK to the player (`tod_reach::can_reach`: never below a drop) and the ENGINE
  agrees (`CanPath`, at most 2 queries a spawn);
- it is in an enabled, active zone that allows spawning (stock's own riser rule), so a disabled
  zone or a room behind a shut door never raises one;
- never inside 360 units of any player, downed players included;
- never inside a live safe-zone field, and a player standing in one is never the focus;
- never in the Battle Arena, never during the finale's aggro run, an arena trip or a card pause;
- the crown rules: nothing beyond a shut causeway gate, nothing on the crown island after the
  Fall seals it, only the hall once the crown seals;
- one ambush round the same player at most every 0.6 s, so no wall of zombies appears at once;
- the ring fits inside THE HUNT's "too far" bar (900 + 4 x 192 = 1668 of walking cost against
  2400), so `_tod_stray` never relocates an ambush spawn as FAR.

**The cost.** One navmesh query a player every half second at most, 64 sampled points, at most 4
zone lookups and 2 path queries a spawn. The zone test moves ONE persistent probe entity (stock's
own `check_point_in_enabled_zone` pattern) instead of spawning one per lookup.

## 3. THE TRICKLE: the rate

`_tod_endless_rounds.gsc`: `TOD_SPAWN_MULT` 0.70 (was a bare 0.83), `TOD_SPAWN_FLOOR` 0.20 (was
0.25), `TOD_RAMPAGE_SPAWN_FLOOR` 0.16 (was 0.20), and the round size `TOD_ROUND_MAX_AI` 28 /
`TOD_ROUND_AI_PER_PLAYER` 7 (stock 24 / 6). The Fall's x0.7, the breather lounges' x1.19 and the
finale's own floor are unchanged.

Measured by `tools/test_ambush.js` over every round 1-60 and every party size, against map 1:

| | Result |
|---|---|
| Zombies a second | at least x1.19 everywhere, x1.25 at depth |
| Round length | x0.93 to x1.01 of map 1's |

Spawn delay, seconds per zombie:

| Round | Solo before | Solo now | 4 players before | 4 players now |
|---|---|---|---|---|
| 1 | 1.66 | 1.40 | 0.56 | 0.47 |
| 10 | 1.05 | 0.88 | 0.35 | 0.30 |
| 20 | 0.63 | 0.53 | 0.25 | 0.20 |
| 30 | 0.38 | 0.32 | 0.25 | 0.20 |

Zombies per round, solo / 4 players: round 10 33 -> 38 / 78 -> 91; round 20 60 -> 70 / 240 -> 280.

Side effects, both small and both by design: more kills a round pay more points a round (the
same per kill); the co-op door price multiplier reads stock's zombie count, so it moves about 1%
(duo 1.27 -> 1.29, trio 1.82 -> 1.84, quad 2.36 -> 2.39). Solo door prices do not move.

Zombie MOVEMENT speed is unchanged (`_tod_zombie_speed.gsc`). The user tuned it down four times
on the first map; a faster ramp is a separate call.

## 4. Knobs per symptom

| Symptom | Knob |
|---|---|
| Too hectic or not hectic enough overall | `TOD_SPAWN_MULT` (working band 0.65-0.90), `TOD_SPAWN_FLOOR` |
| Rounds feel too long or too short | `TOD_ROUND_MAX_AI` / `TOD_ROUND_AI_PER_PLAYER` (move them with the rate to hold the length) |
| Too many or too few ambushes | `TOD_AMBUSH_PCT_START` / `_FULL` / `_FULL_ROUND` / `_RAMPAGE` |
| Spawns land too close | `TOD_AMBUSH_INNER` (360; keep it at or above THE HUNT's 280) |
| Too many cheap hits from behind | `TOD_AMBUSH_BEHIND_PCT` (35), or widen `TOD_AMBUSH_BEHIND_COS` |
| Arrivals feel bunched | `TOD_AMBUSH_GAP_MS` (600) |
| Performance | `TOD_AMBUSH_SCAN`, `_PROBES`, `_CACHE_MS`, `_SPACING` |
| Switch it off | `TOD_AMBUSH_PCT_START`, `_FULL` and `_RAMPAGE` to 0 (corners only) |

## 5. The gate

`tools/test_ambush.js` (in `build_map.ps1` after THE PURSUIT's gate) runs the SHIPPING GSC
through `tools/sky_ships/gsc_eval.js`: the share, the direction roll, the bucket rule, the try
order, the legality filter on the real generated drops / crown / arena data, the focus pick, the
pick end to end (a 1,200-pick run: the share, the split, the spot fields, the facing, the
distance, the log line), the gap, the fallback, the zone rule, the path-check budget, the guards,
the path agent, the hook through `finale_spawn_selection`, and `tod_spawn_delay` against map 1.
Then lockstep with THE HUNT and the generator, the wiring (including the import graph: nothing
the module imports may reach back to the round module), and 24 mutants of the shipping code,
each of which must be caught.

## 6. Diagnostics (dev)

`[TOD_AMBUSH]`:

- `INIT rev=1` with every knob;
- `PICK` for the first 40 ambushes: asked and got direction, distance, height, view dot,
  `seen`, zone, path probes, the round share and the bucket sizes, and the spot;
- `SUMMARY` every 15 s while anything happened: `pool` (left to the corners by the share roll),
  `ahead` / `behind` / `flank`, `fallback`, `no_focus`, `no_ring`, `no_spot`, `zone_fail`,
  `path_fail`, `no_actor`, `agent_self` / `agent_other`.

What to read in the user's log: `agent_self` should carry the count (stock calls the hook from
the zombie's own spawn thread; `agent_other` means it did not and a live zombie answered the path
check instead); `zone_fail` and `path_fail` against the picks show how often the navmesh ring
lands somewhere stock would not spawn; `no_ring` means the query returned nothing.

## 7. Not verified

Native behaviour has not been seen: the navmesh query and `CanPath` on the real mesh, the
climb-out on stair treads, the zone probe in the engine, whether the hook's `self` is the zombie,
the cost at depth, and above all the feel. The gate proves the decisions, not the experience.
