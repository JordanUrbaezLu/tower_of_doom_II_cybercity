# 200 — THE PURSUIT: zombies always get to you, and you can't hide where they can't

**Date:** 2026-10-02 · **Owner:** this session (user: "you're gonna own this") · **Status:** built (-GscOnly BUILD OK 15:31, FF 228,268,480 B), unplayed

> User: *"zombies not being able to trace or target players … many places where you can jump off and you
> can't get back on unless you do some special movement … zombies don't have these animations … we're up
> and down and zombies will be super far away. We need a foolproof solution … The other map had the kind of
> solution, but I think the distance … was a little bit too big … cut that distance … more fast-paced
> instead of waiting around when you try to teleport."*

## 1. What was actually wrong (evidence, not guesses)

| Cause | Evidence |
|---|---|
| **The 24 broken drops are one-way.** The broken-tower pass (2026-09-27) split the tower's navmesh into 25 sections that zombies can go *down* through (native `zm_jump_down_190`) but never up. The zone graph between laps is two-way (`add_adjacent_zone` with no `one_way`), so while you stand on a drop's ledge the floor *below* is an active zone and stock raised zombies on its catch deck — under you, with no way up. | 2026-10-01 runs: a zombie born on lap 43's catch deck (z 16130) while the player stood on the ledge (z 16320); another on lap 19's deck. The engine's own `CanPath` = 0 both times. Zombie 44 *did* drop 18254 → 18049 chasing the player down (the traversal works). |
| **Targeting picked the straight-line-nearest player**, reachable or not (`tod_closest_player` → `ArrayGetClosest`). | Code. A zombie under a drop chased the player on the ledge above instead of a reachable teammate. |
| **The inherited relocator (`_tod_stray` rev 1, TOD1's) was blind to drops and too slow.** It rescued a zombie only at ~4 floors of separation (cost 6000) after 8 s; a zombie on the deck under you scored "near" and was never moved; and its destinations could be below a drop again. | Code + the user's report. |
| **Nothing caught a player who left the playable space.** Stock kills an out-of-bounds player — but not through god mode, and not someone standing somewhere *inside* a zone where zombies can't reach. | 2026-09-30 17:56 run: a Breacher launched off the terrace and fell past the tower for 25 s (z 19,392 → −131,161). |

## 2. The design — four parts, one model

All four ask one question, answered by **`_tod_reach.gsc`**: *can something standing at A walk to B?*

- **Regions** no zombie crosses: the **tower** (Undercity, plaza, all 50 laps, crown stair, terrace, top bay),
  the **crown island** (the jump pad is one-way and players-only), the **Battle Arena**.
- **The chain:** every lap transition is a **cut** — a paid **door** (passable both ways once its zone flag is
  set) or a **drop** (down only). Door *k* sits on floor *k−1*'s landing (cut at z+8, between the landing and
  the first 12-unit tread); drop *k* sits between the catch deck (+2) and the ledge (+192) (cut at +96); the
  roof door at 19200+8. A walk from A to B crosses the cuts between their heights: legal iff no crossed door is
  shut and, going **up**, no crossed cut is a drop.
- Cheap: two binary searches over 51 cuts and two prefix-sum lookups per question. Doors only open, so the
  "shut doors" table is rebuilt only when a door opens.
- **Fails open:** anything it can't vouch for answers "reachable" — the failure mode is stock behaviour.

| Part | File | What it does |
|---|---|---|
| **Spawn filter** | `_tod_endless_rounds::finale_spawn_selection` → `tod_reach::filter_spawns` | Drops every riser from which no player can be walked to (root fix for the drops), then **prefers risers within the hunt's bar (cost 2400) of a player they can reach** — a far riser would raise a zombie the hunt moves 3 s later. Both steps fail safe (an empty result keeps the previous pool). |
| **Targeting** | `tod_closest_player` → `tod_reach::closest` | A zombie chases the nearest player it can **reach** (by walking cost, 2D + 4×height). Never undefined. |
| **THE HUNT** | `_tod_stray.gsc` rev 2 | Zombies that can reach nobody move after **1.5 s**; zombies more than **~1.5 floors** (cost 2400) from every reachable player move after **3 s** (TOD1: 4 floors, 8 s). Stuck-near zombies are checked against the engine (`CanPath`). Destinations: a riser that can reach the player — or any navmesh point in a ring round him — engine-checked, unseen first. They **climb out of the ground** (stock's rise). A zombie on someone's screen isn't moved until desperate (6 s), then **dissolves** (the doors' derez). Last resort: refunded despawn after 15 s. Any player teleport (pads, arena, recall, jump pad) triggers a 12 s rush. |
| **THE RECALL** | `_tod_recall.gsc` rev 2 | **Only a fall off the map** (user 2026-10-02, evening: *"Teleporting to safety should only be when you fall of the map completely. Im fine with players trying to hack and jump down all the way. But if they fall off they should spawn where they came from and at 1 HP"*). Returned to where he came from (his last safe spot) at **1 HP** (a downed player keeps his last stand), with the teleporter's own flash/derez/warp. Never killed. FALL: falling, two floors below the last safe spot, **and nothing under him** (five traces straight down find no surface above the void line) → at once. VOID: below z −448 (under the Undercity floor, over the sealed sky floor) → at once. OFF THE MAP: standing in **no zone at all**, enabled or not (a roof, an ornament, the crown's underside) → after 1 s. **Allowed now:** dropping any number of floors onto the tower, landing below an unbought door (stock's out-of-playable kill is spared there; kill brushes still kill), standing on a ledge no zombie can reach. Rev 1 (15:13) also returned those three cases (FALL with no floor test, OUT OF BOUNDS = outside every *enabled* zone, PERCH = out of a zombie's 64-unit swing). |
| **Elites** | `_tod_bosses::pick_spawn_point` | Every elite spawn and relocation (Doppelghast, Mangler) refuses a spot that can't walk to its anchor. |

**Never judged by the recall:** the jump-pad flight, an Archer's rope and its grace, a frozen player (card
deal, shop spin, class terminal, station), the world pause, and the half second after any script teleport.
A "script teleport" is a move bigger than 600 units in a 0.2 s sample **that the player's own velocity
cannot explain** — a long fall passes 3,000 u/s, and a distance-only test would have read every tick of a
void fall as a teleport and never judged it.

## 3. Tuning — one knob per symptom

| Symptom (from a playtest) | Knob | Where |
|---|---|---|
| Zombies still trail too far behind | `TOD_STRAY_COST` (2400) ↓ **and** `TOD_REACH_SPAWN_NEAR` to the same value (gated lockstep), `TOD_STRAY_PATIENCE` (3000) ↓ | `_tod_stray.gsc`, `_tod_reach.gsc` |
| Zombies pop in *too* aggressively | `TOD_STRAY_COST` ↑ (gate pins ≤ 3000), `TOD_STRAY_PATIENCE` ↑ | same |
| Unreachable zombies linger | `TOD_STRAY_UNREACH_MS` (1500) | same |
| Visible "vanishing" bothers you | `TOD_STRAY_DESPERATE` (6000) ↑, `TOD_STRAY_SEEN_DIST` (2200) ↑ | same |
| After a teleport the horde is slow to arrive | `TOD_STRAY_RUSH_TICK` (10) ↑ | same |
| Void falls return too early/late | `TOD_RECALL_FALL_Z` (768) | `_tod_recall.gsc` |
| Someone stuck on a roof/ornament is returned too fast or slow | `TOD_RECALL_OOB_MS` (1000) | same |
| The fall costs too much / too little | `TOD_RECALL_ARRIVAL_HP` (1; the user's number) | same |
| A real floor under the edge is missed by the floor test | `TOD_RECALL_FOOT_R` (16) ↑ | same |
| Turn the recall off entirely (A/B) | `TOD_RECALL_ENABLED` 0 | same |
| (Lockstep, gated) the map's lowest floor moves | `TOD_RECALL_VOID_Z` (−448) must stay between gen `UC_Z` and `SKY_FLOOR` | same + `gen_tower_map.js` |

## 4. Diagnostics (dev mode, automatic)

- `[TOD_REACH] INIT rev=1 cuts=51 drops=24 doors=27 …`, `DOORS watching=… shut=…`, `DOOR_OPEN flag=…`,
  `SPAWN_FILTER picks= unreachable_risers_dropped= far_risers_skipped= all_unreachable_fallbacks=` (every 15 s, only when it did something).
- `[TOD_HUNT] INIT rev=2 …`, one `MOVE lane=unreach|far|idle|idle_nopath waited_ms= seen= dest=riser|navmesh
  from=(…) tower:<cell> to=(…) tower:<cell> target=<n> … cost_after=`, `RECYCLE …`, `NO_DEST …` (throttled),
  `PUMP`, `RISE_FORCED`, `SUMMARY totals: …` every 15 s.
- `[TOD_RECALL] INIT rev=2 … void_z=-448 … arrival_hp=1 volumes=<n> wrapped_prev_cb=1`, `RECALL why=fall|void|oob
  src=safe|last_valid from=… to=… hp=<before>-><after> downed=… count=…`, `BELOW_DOORS player= zone= at=`
  (a player standing in a not-yet-enabled zone, i.e. who dropped past an unbought door: allowed since rev 2,
  one line per zone entered), `FAIL …` (once per streak), `GIVEUP …`.
- Cells read as `tower:<n>` (n = cuts below the point: 0 = plaza/Undercity, 51 = above the roof door),
  `crown`, `arena`. The existing `[TOD_AI]` tracker (route/path probes) still runs beside them.

## 5. Gates

`tools/test_pursuit.js` (build gate, 158 checks since recall rev 2): runs the **shipping GSC** through the in-repo interpreter
against the real generated drop/door/crown/arena data — all 24 drops both ways, doors shut/open, regions,
fail-open edges, the spawn filter, reachable targeting, the hunt's lanes and destination filter, the recall's
verdict (rev 2: a fall onto the tower is never judged, twenty floors down included; the void line; off the map
held in the air so a hop can't dodge it; standing below unbought doors is never returned; 1 HP on arrival) —
plus lockstep with `gen_tower_map.js` (the void line between `UC_Z` and `SKY_FLOOR`, the arena above it), the
wiring, and **14 mutants of the shipping code that must each be caught** (incl. rev 1's fall-without-floor-test
and the docs/202 haven guard). Arity and native-API gates cover the modules (every engine call has same-VM stock evidence).

## 6. Not verified yet (the user's playtest)

Native behaviour: climb-outs at synthesized navmesh spots, `CanPath` on destinations, the recall's feel, the
floor test at real ledge edges, how spawning and the hunt behave for a player standing below unbought doors
(reachable only since rev 2), co-op splits. Read the `[TOD_HUNT]` / `[TOD_RECALL]` / `[TOD_REACH]` lines from
the archived `console_mp.log` after the session.

**Try:** stand on a drop's ledge for a while (nothing should rise on the deck below); drop and keep
descending (the horde should keep up within a floor and a half); jump straight down several floors onto the
tower (no return); jump off the outside into the void (back where you jumped from, at 1 HP); ride a
teleporter (the horde should arrive in a few seconds); Breacher-launch off the terrace (return at 1 HP, not
death); co-op: one player above a drop, one below.

## 7. Known limits

- The model treats the crown island and the arena as one cell each; their inner doors are covered by the
  engine check (`CanPath`) in the hunt's idle lane and destination filter, not by the model.
- A navmesh island the player can reach but zombies can't (none exist today — the navmesh gate requires
  one component per section) would not trigger a recall; the hunt would log `NO_DEST lane=idle_nopath`.
- Since recall rev 2 nothing returns a player from a spot zombies can't swing at (the perch rule is retired
  on the user's word). If camping on such a spot shows up in play, the hunt still brings zombies as close as
  the navmesh allows; bringing back a gentler perch rule is the user's call.
- The zone graph itself is unchanged (drops are still two-way adjacencies); the spawn filter handles it.
  Making drop adjacencies `one_way` is a possible follow-up, but zone volumes overlap by 200 units, so the
  ledge player still occupies the lower zone and the filter would be needed anyway.
