# 218 - The Archer, pushed toward automatic: the automatic bow, the repeater, the grapple's invisible wall (2026-10-05)

## The ask

User, after an Archer run (archive `tmp/elite_tracking/runs/20261005_202140_164_ff8f34f8`):

> the automatic guns on the first map were just so much fun ... we'll start with the archer first ... you hold it
> down and then once it's fully charged it shoots ... we need abilities where that hold down is a lot less so that
> almost like when it's maxed out it almost becomes an automatic bow ... it just shoots so slow ... the shots don't
> go far enough ... The grapple, you can kind of just go out of the map ... I wonder if we need to build some
> invisible walls.

What that run showed: every arrow left on a RELEASE (holds of 2-4 s just sat at full draw), a tap cycled in ~0.6 s
and a full draw in 1.65 s; arrows were `Ballistic` at 2500 u/s (576 u of drop over 3000); and at 425 s a short
grapple on floor 42 hooked the core wall ~280 above the stairs, "arrived", kept 895 u/s outward over the rail
(whose clip stops 168 above its step), fell to z -1020 and was Recalled at 1 HP.

## What the player gets

| | before | now |
|---|---|---|
| Bow, trigger held | draws, then waits for the release | **fires by itself at full draw and draws again**: one full-power arrow every 0.85 s |
| Bow full draw / release | 1.2 s / 0.45 s | 0.55 s / 0.30 s (packed x0.8) |
| Fire Bow, held | 1.25 s per full-draw arrow | **0.70 s** (packed 0.56 s); splash scaled so its damage per second is unchanged |
| Crossbow (tier 2) | one bolt, then a 1.15 s reload | **a held repeater**: 10-bolt magazine (13 packed), 0.35 s a bolt, 1.6 s reload |
| Arrows / bolts | Ballistic arc, 2500 / 4528 u/s | **flat** (guidance None), 4500 / 5000 u/s, x1.6 at the top of QUICK DRAW |
| QUICK DRAW | x2 at Lv9 | **x3 at Lv9**, every level the same +13% (3^(Lv/9)) |
| QUICK DRAW at Lv8-9 | a 0.83 s full-draw cycle | **0.32 s** (bow), 0.21 s (packed Fire Bow): an almost automatic bow |
| Grapple | could fling you over the rails | **an invisible wall at the edge of the play area**; a hook outside it is refused ("Can't grapple out of the map") |

DPS stays EVEN with the other classes at every tier (the pin now counts a held full-draw arrow, below): per arrow the
bow hits about half as hard and fires about twice as often. QUICK DRAW grows that x3 by Lv9 (it was x2).

## How

**The engine releases the arrow.** `chargeShotFireWhenQueueReachesMax 1` on every bow form (the deffile's own words:
"fire the charge shot weapon automatically when it reaches max bullet queue"). Stock's Skull of Nan Sapwe
(`wpn_t7_zmb_dlc2_keeper_head.gdt`) and this map's Necromancer skull ship it with `chargeShotMaxLevel 1`.
`holdFireTime` (the pull-back clip's length) = `chargeShotMaxTime`, so the arrow leaves the moment the string is back.
UNPROVEN until the playtest: that the engine DRAWS AGAIN while the trigger stays down (the skull's beam is scripted,
so it does not show this). `[TOD_ABOW] HOLD_STALL` says so if it does not; fallback below.

**A held arrow is a full draw by definition** (`_tod_archer_bow::shot_frac`): an arrow that leaves while the trigger
is still down was released by the engine at full draw = x3. A released arrow is timed as before. The clock cannot do
this job: at Lv8+ the whole draw is ~0.1 s past the minimum (two server frames). After a held arrow the next draw
starts when its release clip ends (`now + fireTime`), so a later partial release is timed from there.

**QUICK DRAW = 3^(Lv/9).** The weapon carries the cadence at Lv2 / 4 / 6 / 8 (`SHOTSPEED_STEP` = 3^(-Lv/9): 1 /
0.7834 / 0.6137 / 0.4807 / 0.3766, the same five forms as before: the registration ledger stays at 206). An odd level's
+13% is paid as arrow / bolt damage (`quickdraw_mult`, x1.1298), so no level buys nothing for a player who just holds
the trigger. The script draw window now EQUALS the weapon's at every level (it used to run ahead at odd levels).

**The pin** (`gen_tod_twins.js gunCycle`): an auto-release bow's sustained fire = (fireTime + chargeShotMaxTime) at
`AUTO_DRAW_FULL_MULT` 3 (LOCKSTEP `TOD_AB_MAX_MULT`). Bow 351 / 1053 per tap / full arrow (packed 506 / 1518), Fire Bow
836 / 2508 (packed 1177 / 3531), crossbow 1118 per bolt (packed 1436), all within 0.1% of TIER_SUSTAINED.

**The invisible wall** (`_tod_archer.gsc` `in_play` / `wall_column` / `wall_cut` / `wall_step`): the zone volumes are
the play area (they end at the rails' outer face; every navmesh face sits inside one; THE RECALL calls "no zone" off
the map). On the rope and in the air after it, the HORIZONTAL part of the velocity that would carry the chest out of
every zone over OPEN AIR is removed axis by axis (you slide along it like a wall). Solid ahead (the core, a hall wall)
is the world's to stop. Never vertical (no roof: above the zones, the column you came up is judged), never a teleport,
never on a jump-pad flight, nothing once already out (the Recall and the out-of-bounds return own that). Only the
Archer's rope: other classes keep the open tower (user 2026-10-02: "Im fine with players trying to hack and jump down
all the way"). A hook counts as in play when its arrival point is in a zone volume or straight above one at the
archer's chest height (`hook_in_play`: a high wall inside an open-top hall is fine); past the rails it is refused. `in_play` is stock's own method (`check_point_in_playable_area`: a bare script_model probe + IsTouching
every player_volume), cached, last volume first.

## Logs (dev or `level.tod_diag`)

- `[TOD_ABOW] INIT rev=cyber_bow_auto_v2 ...` - every knob.
- `[TOD_ABOW] FIRE ... auto=1|0 frac= mult= draw_ms= qd= held_arrows=` - auto=1 is an arrow the engine released.
- `[TOD_ABOW] HOLD_END ... held_arrows=N held_ms=` - one line per hold that auto-fired. **N > 1 proves the redraw.**
- `[TOD_ABOW] HOLD_STALL ...` - the trigger stayed down a full draw past an arrow with no next arrow: the engine wants a
  re-press. If this appears, the fallback is to make the bows `Full Auto` with the draw folded into fireTime (no draw
  choice) or to reconsider; tell the user, do not paper over it.
- `[TOD_ABOW] HIT ... qd=` - the QUICK DRAW term on the hit.
- `[TOD_ARCHER] WALL player= axes=x|y|xy org= vel_in= vel_out= grappling= grace= above_zones= walls=` (throttled 4 / s),
  `GRAPPLE_END ... walls=N`, `GRAPPLE_OUT_OF_BOUNDS arrive=` + `REFUSE ... reason=out_of_bounds`.

## Knobs

- Base speed: `cc_bow` / `cc_fire_bow` / `cc_crossbow` `tune.set` in `gen_tod_twins.js` + `TOD_AB_PLAIN_* / FIRE_*` (the
  gate fails if they drift).
- QUICK DRAW top speed: `SHOTSPEED_STEP` (+ `shot_step_lv`, `TOD_AB_QD_LEVEL_MULT`, the Lua `DETAIL[35]` S / D tables).
- Arrow speed: the `projectileSpeed` in tune.set / setUp and `SHOTSPEED_VEL`.
- The wall: `TOD_ARCHER_WALL_LOOK` / `_PAD` (how early it catches).

## Gate

`node tools/test_archer_autobow.js` (in build_map.ps1 after the Archer equipment gate): the shipping pure GSC run
verbatim through `tools/sky_ships/gsc_eval.js` (QUICK DRAW curve, windows, the held-arrow rule, the wall's column and
cut against a box model of the tower incl. the user's floor-42 swing), every one of the 120 emitted Archer forms
against the script, the generator tables, the Lua rows and the card text. Six mutants caught (window drift, a roof,
a clock-timed held arrow, the old x2 table, a stale pause row, the wall unwired). `test_starter_weapons.js` counts a
held full draw for an automatic bow (the old tap rule kept as a negative control); `test_ability_fx.js` retired the
"release now" tick (the bow releases itself at that moment).

## Status

Built: see `docs/status_log.md`. UNPLAYED - the user judges the feel; the logs above answer the one engine question.
