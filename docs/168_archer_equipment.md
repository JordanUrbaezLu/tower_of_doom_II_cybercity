# Archer: Hell's Retriever, grapple, no fall damage

User contract, 2026-09-24: Archer has Hell's Retriever as lethal, grapple as
tactical, and takes no fall damage. A grapple attaches to a visible surface
and launches the Archer toward it. The user tests; the agent builds and logs.
Internal class key remains `assault`. Equipment is granted at every tier,
including before the first upgrade card. Dev and god remain enabled.

## Controls and initial tuning

- Lethal: BO2's native Hell's Retriever offhand, with original hold/throw
  animation, charge stages, native initial projectile, chained attacks,
  power-up retrieval, round-based damage and five-second recharge after catch.
  The original acquisition flourish plays on first equip. See
  [native BO2 contract](170_archer_native_bo2.md) for exact source rules.
- Tactical: aim at solid visible scenery, tap to grapple, tap again to release.
  Range 128-3000 units; pull speed capped at 1300 units/sec, three-second maximum.
  Misses, sky and too-close shots consume nothing. Release preserves momentum;
  arrival/obstruction brakes. Player movement retains normal engine collision.
- No fall damage for Archer, regardless of equipment upgrades or dev/god flags.
  This does not grant immunity to enemies, explosives or death volumes.
- Grapple recharges in 12 seconds from successful attachment. GRAPPLE upgrade
  ranks reduce that to 10 / 8 / 6 seconds. Stable domain key `distraction` and
  id 41 are retained, but the old Cymbal Monkey grant/reconcile is retired.
- HUD: equipment silhouettes mean ready, ACTIVE means in use, numbers show seconds left.
  The standard gun ammo display remains. Menus freeze both recharge clocks;
  held menu inputs cannot cast on dismissal. Opening a menu detaches a grapple.

## Implementation and reuse

`_tod_archer.gsc` owns grapple input, state, fall damage, movement, presentation and
HUD events. A single level-owned 20 Hz loop handles all players, including
disconnect cleanup. Spawn dispatch resets state and deletes old projectiles.
Death/downing/class change clean up active equipment; teleports, mantles and
jump-pad ownership stop the pull. The Athlete movement loop yields to grapple.

Stock `scripts/shared/weapons/grapple.gsc` provides the trace/target precedent,
but its pull is engine behavior requiring a native grapple weapon and authored
targets. That weapon is absent from the installed source database. This version
uses verified BO3 `BulletTrace`, `SetVelocity`, `MoveTo`, and damage callbacks
to support ordinary aimed surfaces. It is a directional pull, not a recreation
of Pathfinder's complete swing simulation.

The Retriever uses `_tod_retriever.gsc` and the native `tod_archer_retriever`
weapon. BO2's original scripts and weapon definition replace the former
simplified Hellbound-derived manual axe. Native offhand events own lethal
input. First-person models, hands, hold/throw/flourish clips, original audio,
charge/trail/impact FX and an animated ember material are integrated. The
custom grapple uses a native first-person inventory item with raise/hold/lower
clips, wrist housing, Apex hook, braided cable, audio and target marker.
The original primary is restored after either equipment presentation ends.
BO3's shader translation is documented in docs/170; pixel-identical rendering
across engines is not claimed.
No donor repository or installed game files are edited.

The playable-area callback spares brief grapple flight (six seconds from
attachment), chains the existing callback, and never overrides a kill brush.
This is necessary because stock Zombies can punish otherwise harmless air
outside a zone volume. It does not unlock doors or permanently exempt Archer
from out-of-map protection. Surface visibility alone is not a guarantee that
the destination is inside the current playable zones.

## Diagnostics and verification

Automatic dev lines use `[TOD_ARCHER]` for grapple, fall and view transitions,
`[TOD_RETRIEVER]` for native pullback/charge/throw/impact/hit/return/catch and
inventory repair, and `[TOD_ARCHER_C]` for the replicated cable. Owner ids,
coordinates, charge, round, damage and failure reasons are recorded at state
changes; there is no per-frame spam. Details and source checks: docs/170.

`node tools/test_archer_equipment.js` executes the shipping GSC scalar decision
functions and checks integration/lifecycle contracts. Native build/link and
deployment results are recorded below. Static checks cannot establish the feel
of the pull, model visibility, native HUD layout or co-op replication.

User playtest: pick Archer; try wall, floor and ceiling grapples, sky misses,
close misses and releasing mid-pull; throw into crowds and a wall; open a card
menu during both abilities; fall onto a valid floor; try a jump pad and a
teleporter; test down/revive/respawn with god off when ready. Archive the resulting
`console_mp.log` with `tools/capture_ai_logs.ps1` before interpreting runtime.

Current build/deployment status is recorded in
`docs/archer_equipment_evidence/build.json`; native-source parity checks are
in `native_sources.json`. The archived user log revealed that the earlier
00:34 build could not boot: `LoadFX` is not a BO3 GSC builtin. That call is
replaced with precached native FX paths and covered by a regression test.
Do not use the old compile success as evidence of a successful playtest.

No agent-run match is authorized. The user tests; preserve their resulting
console with `tools/capture_ai_logs.ps1` and inspect the new diagnostic events.
