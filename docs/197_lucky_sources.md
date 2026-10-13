# 197 — The lucky sources: the Lucky Clover, the Lucky Meteor, the Golden Zombie

> **RESOLVED BUILD NOTE (2026-09-29 ~19:20):** a peer's full build that started 19:18:51 (`tmp/sky_cohesion/full.log`)
> stopped at "Lucky effects are stale": the lucky checks had landed in `tools/build_map.ps1` 18 s earlier, before the
> effects and sounds existed. The wiring was pulled out at ~19:25 (that session re-ran clean at 19:26) and went back in
> with `tools/lucky/wire.py` in ONE step right before session 2a's own build, with every asset present and every check
> passing. RULE: wire last.

**Status: BUILT (FULL BUILD OK 21:18:00, tmp/lucky/full2.log, .ff 21:16:17, FF 225,416,256 B). UNPLAYED - the user tests.**
Every lucky check passed before the link; after it, every model compiled with every triangle and all 10 lucky assets are
in the ledger. Not verified: the sounds inside the bank (see the CHANGELOG entry) - the first playtest confirms them.

**Second pass (21:30-21:53, user: "Golden zombie make one per round" + "It should have a golden glow"):** one golden
zombie EVERY round (was a 1% roll), never lost to something the players did not do, a ~4x brighter gold self-glow, a
bigger aura glow and a REAL gold light that moves with it. BUILT in the peer's FULL BUILD OK 22:22
(`tmp/sky_simplify/full.log`, .ff 22:20:29, FF 225,465,792 B): every lucky check before and after the link passed, and
the three glow maps were re-converted fresh. UNPLAYED. Details are in the CHANGELOG 21:55 entry.
See it without the game: the lucky Blender studio (port 9888) shows it live (`tools/lucky/03_golden_viewer.py`, then
`04_viewer_clean.py` and `05_viewer_light.py` through `mcp_call.py`).

**Played (2026-09-29 23:54, the user's first golden-zombie run):** one golden per round (rounds 1-6), every kill paid
3 bars, one LOST (no player killer) re-issued, 0 script errors. User: *"The glow on the golden zombie is way too
intense"* -> **00:06 glow cut** (model self-glow 2.7 -> ~1.0, chest halo 120 u / 0.5 -> 70 u / 0.2, floor light
700 / 180 u -> 300 / 140 u). Build queued behind the running game: `tools/lucky/build_when_idle.ps1` (status
`tmp/lucky/status.json`, log `tmp/lucky/full4.log`).

## What the user asked for (2026-09-29)

- *"I do want to make [luck] more skill-based ... Can we create a new drop? Which is just a luck drop. Which gives you
  maybe like three luck bars."* Three bars = three of the luck bar's ten segments = 30 (confirmed: "Yes").
- Kill luck: *"Make it 12%"* (a fair-share round of kills paid 18). **Built** (-GscOnly BUILD OK 18:34:47).
- *"Maybe shooting asteroids out of the sky or ships."*
- *"I would like to add a golden zombie that has a 1% chance of spawning and give 3 bars to the killer. But we need a
  new model for this. Build this, lucky meteor and lucky die drop. It should be a lucky clover model and act just like
  regular drops that have the white glow."* / *"Things like perk bottle pap all have the white glow, Zombie blood."*
- *"This model should be consistent with other drops like pap and perk bottle and zombie blood so it seems like it
  comes from this game"* / *"why would you make it gold. The others arent gold."*

## The three sources

| Source | What the player sees | Reward | Code |
|---|---|---|---|
| **Lucky Clover** (a drop) | A four-leaf clover charm floating with the same pale white glow as the perk bottle / PaP / Zombie Blood drops | The grabber gets 3 bars, segment by segment, with the bar's rising pips | `_tod_lucky.gsc` (+ `.csc`) |
| **Lucky Meteor** | Every 2 rounds (from round 3) a burning gold meteor crosses the sky low over the party, announced by a whoosh + chime | Shoot it down: it bursts and the clover falls to the shooter's feet | `_tod_lucky.gsc` |
| **Golden Zombie** | ONE ordinary zombie every round spawns gold (one of the round's first 60% of spawns): glowing gold, gold eyes, sparkling, lighting the floor around it in gold, with a shimmer you can hear; a chime tells everyone one is out there | Its killer gets 3 bars + a jackpot chime | `_tod_golden_zombie.gsc` |

A golden zombie that dies to no player (a nuke, a trap, a script sweep) or is removed without dying is OWED: the next
ordinary spawn, in any round, turns gold in its place (at most two waiting). A golden still alive from an earlier round
does not cancel the current round's.

The clover also drops in the normal random drops at `TOD_CLOVER_DROP_PCT` (50) of a regular drop's share, like the
perk bottle and the PaP drop ("act just like regular drops"). 0 = meteor only.

## The consistency rule (the clover)

The PaP drop (ZoekMeMaar, `skinOverride lambert1 mtl_x2icon_gold`) and Zombie Blood (NSZ, a BO2 power-up port whose
only material is `mtl_x2icon_gold`) share ONE stock material: a black colour map lit only by reflections
(`model_export/t5_props_zombie.gdt`). Despite its name it does not read gold in game. The clover names that same
material, so it is lit exactly like them. It is one solid cast piece (pillowy heart leaves, raised veins, a domed hub,
a curled stem), about 19 x 4 x 21 units (the PaP drop is 17 x 12 x 22, Zombie Blood 10 x 4.5 x 18).
`tools/lucky/verify_native.py` FAILS if the clover ever wears another material or if our GDT redefines the stock one.
Line-up render (the clover between the real PaP and Zombie Blood models, same material and light):
`art/lucky/lineup_front.png`, `art/lucky/lineup_34.png`.

## Files

- `scripts/zm/zm_tod2_cybercity/_tod_lucky.gsc|.csc` — the clover power-up + the meteor director, flight, view-ray shot
  test (the `_tod_secret` bears' form: any gun, bow or staff; the Warrior's fists and blades do not count) and the
  clover's fall to the shooter.
- `scripts/zm/zm_tod2_cybercity/_tod_golden_zombie.gsc` — one per round (stock `add_custom_zombie_spawn_logic` counts
  the round's ordinary spawns; `golden_target` picks the Nth, pure and tested), the owed re-issue, the swap (the
  Necromancer thrall's proven sequence), no limb gibs, the aura, the killer's payout.
- `_tod_luck.gsc` `add_bars( player, n )` — a reward worth N bars, one segment per step.
- Guards: `_tod_sprinter::eligible` and `_tod_necro_summon::is_elite` skip golden zombies.
- `tools/lucky/01_author.py` (Blender MCP, port 9888; `mcp_bootstrap.py`, `mcp_call.py`) — the clover + meteor models,
  `source_data/tod_lucky.gdt`, `art/lucky/manifest.json`, previews. Never hand-edit its outputs.
- `tools/lucky/make_golden.py [--check]` — the golden zombie's gold twin materials + xmodels
  (`source_data/tod_golden_zombie.gdt`, `model_export/tod_lucky/golden/`).
- `tools/lucky/make_fx.py [--check]` — the seven `tod/luck/*` effects (built on the sky fleet's element builder).
- `tools/lucky/make_sounds.py [--check]` — the nine `tod_luck_*` sounds + `sound/aliases/tod_luck.csv`.
- `tools/lucky/verify_native.py [--compiled-ledger]`, `tools/lucky/test_lucky.js [--ledger]` — the gates.

## Knobs

| Symptom | Knob |
|---|---|
| Clovers too common / rare in random drops | `TOD_CLOVER_DROP_PCT` (`_tod_lucky.gsc`) |
| Meteors too often / rare | `TOD_METEOR_EVERY`, `TOD_METEOR_FIRST_ROUND` |
| Meteor too hard / easy to hit | `TOD_METEOR_HIT_R` (must stay >= the rock's farthest lump, 182), `TOD_METEOR_DIST_*`, `TOD_METEOR_FLIGHT_SECS` |
| Golden zombies per round | `TOD_GOLDEN_PER_ROUND` (user: 1); `TOD_GOLDEN_SPAN` (0.6) = how early in the round it can appear |
| Golden zombie too dull / bright | `tools/lucky/make_golden.py` `ALBEDO / SPEC / GLOW / GLOW_SCALE` (the model's own glow: 0.45 x 2.2 since 2026-09-30 00:06; the 0.45 x 6.0 of 21:30 was "way too intense" in game) |
| Its chest halo too big / bright | `tools/lucky/make_fx.py` `golden_aura()` orb: 70 u / alpha 0.2 (120 / 0.5 was too intense) |
| Its gold light too bright / dim / wide | `tools/lucky/make_fx.py` `GOLDEN_LIGHT_INTENSITY` (300; 700 was too intense) / `GOLDEN_LIGHT_RADIUS` (140), then a FULL build |

## Dev logs (with `level.tod_dev`)

`[TOD_LUCKY]` READY / CLOVER_GRAB / METEOR_ROUND / METEOR_WAIT / METEOR_PLAN_FAIL / METEOR_SPAWN / METEOR_HIT /
METEOR_BLOCKED / METEOR_MISS / METEOR_LAND; `[TOD_GOLDEN]` READY / ROUND (the round's target spawn) / ROLL / SKIP /
SPAWN / KILL / LOST (owed=N: the next ordinary spawn turns gold);
`[TOD_LUCK]` RATE / BAR / SPENT / BARS.
