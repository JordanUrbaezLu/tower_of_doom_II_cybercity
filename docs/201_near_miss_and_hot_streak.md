# 201 — NEAR MISS + THE HOT STREAK (the Black Market spin and the card pull)

STATUS 2026-10-02: **IMPLEMENTED (sections 3-6, all three parts in one pass); build in section 10.**
The user approved the plan as written ("Actually yes implement what you came up with. Its fine"), so
the four calls in section 8 took their recommended answers: SLIPPED PAST at 8%, x1.15 / 1.30 / 1.50,
guaranteed cards count, teammates are told at ON FIRE. Section 10 is the as-built record. UNPLAYED.

User (2026-10-02): *"Lets look into the concept of near miss and almost hit that sports companies
and gambling companies use. We want to someone inject this concept in our black market and card flip
systems. Makes sense? Come up with an implementation plan on how we can do this."* Then: *"And also the
hot hand effect as well. We need this in the game as well. Not crazy but a bit too allow for those
crazy lucky games and pull towards players."*

OWNERS: the spin screen and the card reveal belong to session d2 (docs/188, top); the dealer's voice
pipeline is `tools/black_market_vo` (the voice session); 9c owns the companion item EFFECTS, which this
plan does not touch. Ping the owners before editing their files, and never edit while a peer build runs.

## 1. What the research says, and the line we hold

| Idea | Where it comes from | What it does to a player | Our version |
|------|---------------------|--------------------------|-------------|
| Near miss | Slot machines stop the jackpot symbol just above or below the pay line. | Feels WORSE than a plain loss, yet raises the urge to play again and lights the brain's win circuitry (Clark et al. 2009, Neuron 61:481). The effect needs the player to feel in control (they pulled the lever, they chose). | The spin's STOPPED SHORT and SLIPPED PAST (section 3), the card's REACH (section 4). |
| How often | Kassinove & Schare 2001: near misses on 30% of losses kept players going longest; 15% and 45% kept them less (an inverted U). | Too many and they become noise. | About 30%. The spin teases 45% today, silently. |
| Almost hit | Sportsbooks: "one leg away" messages on lost parlays, refunds when exactly one leg loses. Pachinko: "reach" animations that sometimes hit and sometimes fail, and "revival" (looks lost, then hits). | The almost-win is sold as a reason to go again; a reach that can go either way is suspense. | The card's REACH (it can fail or break through); the ONE SEGMENT SHORT readout (section 6). |
| Hot hand | Gilovich, Vallone & Tversky 1985 called the basketball hot hand a fallacy; Miller & Sanjurjo 2018 (Econometrica 86:2019) found a bias in that analysis, and once corrected a modest real hot hand appears. Casinos lean on the belief (hot tables, hot / cold number boards); games make it real and visible (NBA Jam's "heating up / on fire", killstreaks). | A visible streak feels meaningful and pulls the player toward the next play while it lasts. | THE HOT STREAK (section 5). |

**The line.** Deciding a result and THEN choosing to dress it as a near miss is exactly what Nevada
bans in real-money slots (Gaming Regulation 14.040: no "variable secondary decision" after the outcome,
from a 1989 ruling), because it makes the jackpot look closer than it is. This map has no real money,
and the spin screen already shows the TRUE odds, so it is ordinary game feel here. These rules keep it
honest, and the gates in section 7 enforce them:

1. **The result is rolled first, at the odds the game shows.** A near miss only decides what is shown
   around that result. It never changes what the player gets.
2. **Never show a prize and take it back.** The reel never locks (stop clunk, flare) on a jackpot it
   then leaves; a card never fully lights a rung and then drops it.
3. **Only tease what could have happened.** A teased tile is an item this companion would really gain;
   a card only reaches for a rung its headroom allows.
4. **The hot streak is a real odds change, and every place that shows odds includes it** (THE ODDS
   panel, docs/187 section 2, docs/188 section 3, both armory pages).
5. **About 30% near misses, no more.**

## 2. What exists today

- **Spin** (`_tod_shop.gsc` `spin()`): `TOD_SPIN_TEASE_PCT` 45. A non-Legendary prize gets a tile one
  rarity better just past the needle (tile `land + 1`, a random item). Nothing moves toward it, nothing
  sounds, the dealer does not react. A LEGENDARY prize's last step is `TOD_SPIN_LEG_HITCH_MS` 850 ms
  longer with a heartbeat (`tod_pull_beat`), so the heartbeat is a 100% Legendary tell.
- **Card pull** (`_tod_upgrade_ui.gsc` `reveal_deal` / `reveal_slot`, drawn by `TodPull.lua`): every rung
  ends in a heartbeat, so a rung never gives away whether the climb stops there, EXCEPT that a RARE+
  card's final heartbeat is replaced by its sting. The prototype's near-miss toggle (docs/187 section 4)
  was left off.
- **Luck** (`_tod_luck.gsc`): the bar (0..100) sets the odds and is spent by every deal and every spin.
  There is no streak state.

## 3. The Black Market: STOPPED SHORT and SLIPPED PAST

### What the player sees

- **STOPPED SHORT** (22% of non-Legendary spins). The reel crawls in and runs past the prize until the
  needle sits on the seam with the next tile. That tile is better: one rarity up, or a LEGENDARY half the
  time (an EPIC prize always teases a LEGENDARY), and it is an item this companion would actually gain.
  The reel hangs there for 0.4 s: the needle leans toward it, the teased tile glows in its colour, and a
  heartbeat thumps when it is a LEGENDARY. Then it falls back onto the prize. A deflating sting, the teased
  tile's glow drains away, and the dealer winces.
- **SLIPPED PAST** (8% of non-Legendary spins, always a LEGENDARY). The reel crawls onto a LEGENDARY with
  the jackpot heartbeat and sits on it for 0.85 s WITHOUT locking (no stop clunk, no flare), then creeps off
  onto the real prize. The dealer: *"Ohh, it slipped."*
- **The real jackpot** keeps its heartbeat crawl. Side effect, wanted: the heartbeat stops being a 100%
  tell. Measured: a heartbeat is a real LEGENDARY 17% of the time at an empty bar, 25% at 60 luck and 54%
  at a full bar. A real Legendary finally has suspense, and banking luck makes the heartbeat more trustworthy.
- Total: 30% of non-Legendary spins carry a near miss (section 1).

### Server (`_tod_shop.gsc`)

- `near_plan( rar, slots )` replaces the three `tease` lines in `spin()`. It runs AFTER `roll_rarity` and
  `roll_item` and never touches them. It returns `kind` (0 none, 1 STOPPED SHORT, 2 SLIPPED PAST) and the
  teased tile: rarity by the rules above, item `roll_item( slots, tease_rar )`, so the tease is a real gain.
- Knobs: `TOD_SPIN_NEAR_SHORT_PCT` 22, `TOD_SPIN_NEAR_PAST_PCT` 8, `TOD_SPIN_NEAR_LEG_PCT` 50 (STOPPED SHORT
  teases that show a LEGENDARY rather than one rarity up), `TOD_SPIN_NEAR_HANG_MS` 400,
  `TOD_SPIN_PAST_HOLD_MS` 850, `TOD_SPIN_VO_NEAR_PCT` 70. `TOD_SPIN_TEASE_PCT` retires.
- **Wire, no new event:** `tod_spin_open`'s `tease` argument carries `heat * 256 + kind * 64 + tile`
  (tile <= 39, so at most 935; `heat` is section 5's). The fourth argument stays `luck * 64 + land`.
- `step_ms( last )`: STOPPED SHORT adds the hang; SLIPPED PAST makes the last step a hold on the jackpot
  plus the crawl off it. The heartbeat plays in the hang / hold whenever the teased tile is LEGENDARY.
- After the land: `tod_spin_near` (the deflate) and the dealer's near line; log `SPIN_NEAR`.

### Client (`TodSpinReel.lua`)

- Decode the packed `tease`; `tileValue` puts the teased tile at `land + 1` (STOPPED SHORT) or `land - 1`
  (SLIPPED PAST).
- `onStep( last )`, STOPPED SHORT: run past the prize to `P3.NEAR_EDGE` 62 px (tiles are 140 wide on a 150
  pitch and the needle is 24 wide, so the needle sits on the seam), hold for `P3.NEAR_HANG_MS` with the
  needle tilted toward the teased tile and that tile's glow pulsing, then the existing Bounce settle.
- `onStep( last )`, SLIPPED PAST: a no-move tween for `P3.PAST_HOLD_MS` (the jackpot under the needle,
  glowing, the dealer in his watch pose), then the crawl to the prize with no overshoot.
- `onLand`: the teased tile's glow drains over 0.5 s; the dealer's pose is `shrug` until a sixth pose
  (`wince`) is drawn (optional art, docs/195 format, FULL build).
- Every new number goes in the `P3` table: the constructor sits near Lua 5.1's 60-upvalue cap.

### Sound and voice

- `tod_spin_near`: a deflating down-sweep, ~0.6 s. A synthesized placeholder now (a new
  `tools/near_miss/make_sounds.py` with a `--check` gate, like `tools/lucky/make_sounds.py`); the authored
  one in the next sound brief (`tools/sound_kit/install.py` gains the row).
- The dealer's near lines: group `near` in `tools/black_market_vo/lines.json`, four generic takes (in his
  register, for example: *"Ohhh, so close!"*, *"A whisker, my friend. A whisker."*, *"The machine is
  teasing you."*, *"Next time, hmm?"*) plus one per class. Generated with the shipping clone voice (it
  exists: never create it again) through mask v5 (final: never retune it), picked with `pick.py`, 3D rows in
  `tod_shop.csv`, length table regenerated. The voice rules stand: no German words, never his name.

## 4. The card pull: THE REACH

### What the player sees

- Sometimes, after a heartbeat, the card **strains for the next rung**: the next gem on its ladder
  flickers in the next rarity's colour, a sweep of that colour climbs two thirds of the way up the back and
  holds, the card lifts a few pixels and trembles, and a tension swell rises.
- **SO CLOSE:** the swell cuts off, the flicker dies, the sweep drains, the card sinks back and flips at the
  rung it had already reached. Then its sting.
- **BREAK THROUGH:** the sweep completes in a burst and the card jumps to the next rung with a crash. The
  climb carries on.
- SO CLOSE happens on a card's FINAL rung; BREAK THROUGH on the rung BELOW a RARE+ card's final rung. So a
  reach at the purple rung is the moment players learn to love: will it turn gold?

### Who reaches (per card, by its real outcome)

| Card ends at | SO CLOSE at its final rung | BREAK THROUGH from the rung below |
|--------------|----------------------------|-----------------------------------|
| COMMON       | 12% (needs room for +2)    | none                              |
| RARE         | 18% (needs room for +3)    | 10%                               |
| EPIC         | 30% (needs room for +4)    | 25%                               |
| LEGENDARY    | none (no rung above)       | 60%                               |

At most ONE reach per deal: the left card rolls first, the right card can only reach if the left did not.
Measured on the docs/187 odds and guarantees (1,000,000 deals per bar, headroom ignored): a near miss (SO
CLOSE) in 27-30% of deals at every bar, on the section 1 target; a reach of either kind in 42% of deals at
an empty bar, 50% at a half bar and 67% at a full bar (the guaranteed Epic+ cards reach most, so banking
luck buys more drama); a purple reach turns gold 38-42% of the time. The gate re-measures these on the
shipping code (section 7); if full-bar deals feel over-dramatic, lower the LEGENDARY and EPIC break-through
rates first.

Never a reach on: the CLASS TIER card, a floor-locked card (`o.locked`), a rarity-locked domain
(`make_option` sets `o.rarity_locked` beside the existing `rarity_lock` line), a card without the headroom
for the next rung, or the dev CARD TEST bench's random deals.

### Engine (zero new clientfield bits)

- **The wire:** a REACH is a second `todUpgHold` beat at the same rung with no climb in between. The NEXT
  edge resolves it: a CLIMB (the rarity field rises) = BREAK THROUGH; one more BEAT = SO CLOSE (the flip
  follows). The worst-case deal goes from 10 beats to 11, inside the field's 15.
- `_tod_upgrade_ui.gsc`: `reach_plan( opts )` runs in `reveal_deal` (the opts are final by then: rolled,
  guaranteed, clamped). `reveal_slot` takes the plan. At the reach rung the hitch plays the plain thump,
  never the sting (the sting would give the ending away); then `pull_beat()` + `tod_pull_reach` and
  `TOD_PULL_REACH` 0.62 s. SO CLOSE: `pull_beat()` + `tod_pull_reach_fail`, `TOD_PULL_REACH_SETTLE` 0.26 s,
  the rarity's sting + `TOD_PULL_HITCH`, flip. BREAK THROUGH: the rarity push plays `tod_pull_break`
  instead of the rung sound, and the climb goes on. Every wait scales by `TOD_REVEAL_LIVE_SCALE` (x0.5 at a
  live co-op altar) like every other beat. Log `[TOD_PULL] REACH slot= rung= result=`.
- `TodPull.lua`: count beats since the last climb; the second one calls `Reach()`; a CLIMB while reaching
  calls `BreakThrough()` then `Climb()`; a third BEAT while reaching calls `Deflate()`. Every tween must fit
  the gap it can be overtaken in at the live scale (the file's existing rule). LOCKSTEP `PULL_REACH_MS`.
- Knobs: the table above (`TOD_PULL_NEAR_*`, `TOD_PULL_BREAK_*`), `TOD_PULL_REACH`, `TOD_PULL_REACH_SETTLE`.
- The dev CARD TEST bench (`_tod_upgrades.gsc` `dev_card_test_*`) gains three forced deals: an EPIC that
  comes SO CLOSE to gold, a LEGENDARY that BREAKS THROUGH from purple, a COMMON that comes SO CLOSE to blue.
- Sounds: `tod_pull_reach` (~0.6 s swell that hangs), `tod_pull_reach_fail` (~0.3 s deflate),
  `tod_pull_break` (~0.7 s crash and riser). Placeholders now, authored ones in the sound brief.

## 5. THE HOT STREAK (the hot hand)

### The rule

- A **pull** is one card deal (a round event, an altar, a trial reward) or one Black Market spin. The dev
  bench never counts.
- Its **result** is the best card dealt (the CLASS TIER card and a floor-locked card do not count; a deal
  with nothing else changes nothing) or the spin's prize.
- An EPIC adds 1 to your streak and a LEGENDARY adds 2. Anything less ENDS the streak. Going down ends it.
- **Heat = streak - 1, at most 3:** streak 2 = **WARM**, 3 = **HEATING UP**, 4+ = **ON FIRE**.
- **Heat multiplies the EPIC and LEGENDARY odds by x1.15 / x1.30 / x1.50** (COMMON pays for it), on cards
  and on spins. The luck guarantees still read the bar alone. It only ever helps: a miss ends it, it never
  makes the odds worse than normal.

The odds a card or a spin rolls at each heat (before the guarantees; COMMON / RARE / EPIC / LEGENDARY):

| Bar | Cold | WARM | HEATING UP | ON FIRE |
|-----|------|------|------------|---------|
| 0   | 56 / 27 / 13 / 4 (Epic+ 17) | 53.4 / 27 / 14.9 / 4.6 (19.5) | 50.9 / 27 / 16.9 / 5.2 (22.1) | 47.5 / 27 / 19.5 / 6 (25.5) |
| 50  | 46 / 31.5 / 16.5 / 6 (22.5) | 42.6 / 31.5 / 19 / 6.9 (25.9) | 39.3 / 31.5 / 21.4 / 7.8 (29.3) | 34.8 / 31.5 / 24.8 / 9 (33.8) |
| 100 | 36 / 36 / 20 / 8 (28) | 31.8 / 36 / 23 / 9.2 (32.2) | 27.6 / 36 / 26 / 10.4 (36.4) | 22 / 36 / 30 / 12 (42) |

### What it does over a run

`node tools/near_miss/sim_hot_streak.js` (200,000 runs; its header states the run model):

| | Odds effect off (display only) | Mild x1.10/1.20/1.35 | **Pick x1.15/1.30/1.50** | Strong x1.25/1.50/1.80 |
|---|---|---|---|---|
| Legendaries per run | 2.34 | 2.39 | **2.43** | 2.50 |
| Runs with 6+ Legendaries | 2.5% | 2.9% | **3.2%** | 4.0% |
| Runs with 4+ Legendaries | 20.0% | 21.4% | **22.2%** | 24.0% |
| Pulls made while hot | 19.0% | 19.9% | **20.3%** | 21.4% |
| Pulls made ON FIRE | 3.6% | 4.5% | **5.0%** | 6.1% |
| Runs that reach ON FIRE once | 44.7% | 49.2% | **51.2%** | 55.3% |

Reading it: about half of all runs get an ON FIRE moment, and the luckiest games get luckier (a
6-Legendary game goes from 1 run in 40 to 1 in 31) while the average barely moves. That is "not crazy but
a bit". Note the first column: streaks happen on 19% of pulls by chance alone, so the VISIBLE streak
carries most of the feeling, and the multiplier lets a hot run snowball a little.

REJECTED, and recorded so nobody brings it back: "+1 heat per Epic, +2 per Legendary, -1 per miss". The
sim had players hot on 55% of pulls and ON FIRE in 87% of runs: Epics are common (two cards a deal, plus
the luck guarantees), so heat became the normal state and ON FIRE meant nothing. A streak must END on a miss.

### What the player sees and hears

- **HUD:** embers rise off the luck plate (the card reveal's mote sprite tinted orange, 2 / 4 / 6 by heat)
  and a chip beside it in the map typeface reads WARM / HEATING UP / ON FIRE. At ON FIRE the plate's lit
  segments pulse orange.
- **When it rises:** a stamp (HEATING UP, ON FIRE) after the card reveal's last flip or under the spin's
  result, with `tod_heat_up` (an ignite whoosh) or `tod_heat_fire` (a roar). ON FIRE is told to teammates,
  *"NAME IS ON FIRE"*, on the same free lane as the Legendary alert.
- **When it ends:** `tod_heat_out` (a hiss), the embers die, the chip fades. A down does the same.
- **Card pull:** a hot player's backs arrive warm (an orange rim and embers on each back).
- **Black Market:** the LUCK box wears the chip; the pour's motes become embers; THE ODDS shows the heated
  true odds with the caption HOT STREAK - BETTER ODDS; the filler tiles roll the heated odds, so the reel
  visibly runs hotter; at heat 2+ the dealer greets it (*"Hot hands tonight, friend!"*, group `hot`).
- Typeface: every new word uses A-Z, 0-9 and space only (no percent sign; "+" and "/" live in the digit set).

### Engine

- `_tod_luck.gsc` owns it: `player.tod_luck_streak`, `player.tod_luck_heat`; API
  `streak_result( player, best_rarity, source )` and `streak_end( player, why )`; `down_watcher` ends it.
  Precache eventstring `tod_luck_heat` and push `tod_luck_heat( heat, streak )` on every change, on spawn,
  before every deal, and every 5 s while heat > 0 (HUD rebuilds). Log `[TOD_LUCK] STREAK`.
- The odds: `_tod_upgrades::roll_rarity` and `_tod_shop::roll_rarity` read `player.tod_luck_heat` as a
  field (the module cycle rule: neither may `#using` `_tod_luck` for this) and multiply EPIC and LEGENDARY
  by ONE table. `TodSpinReel.lua`'s `effOdds` and `fillerRarity` get the heat from `tod_spin_open`.
  LOCKSTEP: those three, docs/187 section 2, docs/188 section 3, both armory odds tables.
- Reporting: `_tod_upgrade_ui` reports a deal's best card after the reveal through
  `level.tod_luck_streak_fn` (set in `_tod_luck::init`; the upgrade modules cannot import `_tod_luck`);
  `_tod_shop` calls `tod_luck` directly after the land (it already imports it).
- `tod_upgrade.lua` decodes `tod_luck_heat` in its scriptNotify chain into `CoD.TodHeat` and draws the HUD
  layer; `TodPull.lua` reads `CoD.TodHeat` for the warm backs.

## 6. Bonus: ONE SEGMENT SHORT (the honest almost-hit)

At a deal or a spin with the bar at 40..49 or 90..99, one line says ONE SEGMENT FROM A RARE or ONE
SEGMENT FROM AN EPIC: the guarantee the player just missed. It is true information, it teaches banking luck
before a deal, and it is the sportsbook "one leg away" without the trick. Card panel: under the luck badge.
Spin: THE ODDS caption. Measured to fit its box before it ships.

## 7. Build order, previews, gates, logs

1. **The Black Market near misses** (section 3): scripts, Lua, placeholder wavs + alias rows, dealer lines.
   A -GscOnly build (it regenerates the sound banks).
2. **The card reach** (section 4): a -GscOnly build.
3. **The hot streak** (section 5): a -GscOnly build.
4. Optional art (the dealer's `wince` pose; an ember sprite if the tinted mote reads wrong): a FULL build.

Before each build, see it without the game: `render_spin.py` gains `--near short|past` and `--heat N`;
`render_pull.py` gains `--reach A:fail` / `--reach B:win` and `--heat N`. Both run the real Lua on the
server's exact schedule.

Gates (every build):
- `tools/partner_shop/test_spin.js`: `near_plan` never changes the prize (the same RNG stream with near
  misses on and off gives identical prizes); only prizes below LEGENDARY are teased; SLIPPED PAST only with a
  LEGENDARY tile; the teased item is a real gain for those slots; the rates land within 1.5 points of the
  knobs; the packed `tease` round-trips.
- `tools/test_spin_reel.lua`: both endings draw (the needle on the seam, the hold), with negative controls.
- `tools/test_card_pull.lua` plus a GSC check of `reach_plan`: it never edits `o.rarity`, `o.levels` or
  `o.domain`; only eligible cards reach; at most one reach a deal; every deal shape stays within 15 beats;
  the Lua resolves both endings; a reach left unresolved fails (negative control). It prints the measured
  reach, near-miss and purple-to-gold rates.
- NEW `tools/test_hot_streak.js` (shipping functions through `tools/sky_ships/gsc_eval.js`): every streak
  transition (EPIC, LEGENDARY, miss, down, the cap), the multiplier table identical in all three places,
  COMMON never below 0 at any bar and heat, the guarantees unchanged, and the run numbers from section 5.

Logs (dev, automatic): `[TOD_SHOP] SPIN_NEAR kind= tease= heartbeat=`,
`[TOD_PULL] REACH slot= rung= result=`, `[TOD_LUCK] STREAK player= streak= heat= why=`.
Then the user plays and the logs are read.

## 8. The user's calls (the recommended one first)

1. **SLIPPED PAST** (the reel sits on a Legendary, then slides off): keep it at 8% / drop it and keep only
   STOPPED SHORT.
2. **Streak strength:** x1.15 / 1.30 / 1.50 / milder x1.10 / 1.20 / 1.35 / stronger x1.25 / 1.50 / 1.80.
3. **Guaranteed cards count toward the streak** (what the player sees): yes / dice only (hot on 16% of
   pulls instead of 20%, ON FIRE in 38% of runs instead of 51%).
4. **Tell teammates when someone is ON FIRE:** yes / no.

## 9. Not in the first pass (options, off)

- Near-miss insurance (the sportsbook refund): a STOPPED SHORT pays back 5 luck. Off: it changes the
  economy, and the near miss should cost nothing but a feeling.
- More reaches while ON FIRE (pachinko's hot mode). Off: reach rates stay tied to real outcomes only.
- A cold streak or pity timer. The luck guarantees already do that job.
- Heat from other luck events (Lucky Clover, Golden Zombie, a Panzer last hit). Off: pulls only.

## 10. As built (2026-10-02, session -50)

Everything in sections 3-6, with the section 8 calls at their recommended answers. Nothing changes a
result: every roll happens first, at the shown odds, and the theatre is decided from it.

**Files.** `_tod_shop.gsc` (`near_plan`, the heated `roll_rarity`, the long last step, `spin_near_after`,
the packed open `heat * 256 + kind * 64 + tile`), `TodSpinReel.lua` (STOPPED SHORT: run / hang / settle,
SLIPPED PAST: creep / slip, the gold glow, the heated odds + caption, the HOT STREAK chip),
`_tod_upgrade_ui.gsc` (`reach_plan`, `reach_roll`, the reach branch in `reveal_slot`, `streak_report`),
`TodPull.lua` (`Reach`, `Deflate`, `BreakThrough`, `Warm`, `P.EmberStep`), `tod_upgrade.lua` (the HUD heat
layer: orange segments at ON FIRE, embers, the chip; the panel's HOT STREAK and ONE SEGMENT lines),
`_tod_luck.gsc` (`streak_result`, `heat`, `heat_mult`, the `tod_luck_heat` eventstring, the 5 s resend),
`_tod_upgrades.gsc` (`heat_mult_of` in `roll_rarity`, `rarity_locked`, the dev bench's forced reaches).
Sounds: `tools/near_miss/make_sounds.py` -> 8 wavs in `sound_assets/tod/near/` + `sound/aliases/tod_near.csv`.
Dealer: 11 new lines in `tools/black_market_vo/lines.json` (`near` x4, `cls_near` x4, `hot` x3) on the
consented clone with the shipping mask, take 1 shipped by `pick.py`.

**Gates** (both new ones in `build_map.ps1` after the dealer's `pick.py --check`):
`tools/test_hot_streak.js` (106 checks, the shipping GSC through `gsc_eval.js`), `make_sounds.py --check`,
`test_spin.js` (647), `test_spin_reel.lua`, `test_card_pull.lua` (174).

**Logs** (dev): `[TOD_SHOP] SPIN_ROLL ... heat= mult= near= tease=`, `SPIN_LAND ... near=`,
`SPIN_NEAR kind= tease= heartbeat=`; `[TOD_PULL] REACH slot= domain= rung= result= rarity= cur= forced=`,
`STREAK_REPORT`; `[TOD_LUCK] STREAK player= source= best= streak= heat=a->b mult=`.

**Seen before the build** (`render_spin.py --near short|past --heat N --heat-after M`,
`render_pull.py --reach A:fail|A:win|B:fail|B:win --heat N --heat-after M`). The previews caught three
real faults, all fixed and gated:
1. THE REEL'S LEFT TILE VANISHED AT EVERY STEP (old, not new): `placeTiles` filled k-4..k+5, ten tiles
   into nine slots, so k+5 took k-4's slot. Unseen at speed; SLIPPED PAST's creep held the gap on screen
   for most of a second. The window is k-4..k+4 now; `test_spin_reel.lua` fails on the old one.
2. THE WARM BACKS' EMBERS WERE INVISIBLE: they used the under layer's motes, which draw behind the opaque
   card. They are their own elements OVER the back now; `test_card_pull.lua` checks the draw order and
   fails on the old one. The halo went from 0.14 + 0.06 x heat to 0.22 + 0.08 x heat (it read as +20 red).
3. THE REACH'S GOLD READ TAN over an EPIC's purple: the fill is 0.7 (was 0.55).

Also fixed on the way: the deal's LUCK badge latched the first deal's luck for a whole life (`wasShown`
was never reset); the ONE SEGMENT deals in `test_card_pull.lua` guard it.

**Noticed, not changed (not this work):** the LEGENDARY card's gold motes after the flip (docs/187) use the
same under-layer motes, so they are hidden behind the face too. Moving them over the face would put moving
specks over the card text while the player reads it; that is the card owner's call.

**BUILD:** -GscOnly BUILD OK 18:20:38 (tmp/near_miss/gsc2.log; .ff 18:18:40, FF 228,312,000 B; loaded bank 154.5 MB = +3.6 MB for the 8 near-miss sounds and 11 dealer lines, streamed 313.8 MB; the 8 known-waived linker lines only). The new gates ran inside it (HOT STREAK + REACH 106, NEAR MISS SOUNDS 8, SPIN 647, THE PULL 174, the reel harness). Verified: scripts / zone_source / ui deployed = repo, nothing synced after the .ff, the 8 near wavs + 11 dealer wavs deployed = repo, every new stem in the loaded bank, the ledger carries the 5 changed scripts and the 3 Lua rawfiles. The first attempt (tmp/near_miss/gsc1.log, 18:07) linked but its guard FAILED it: BlackOps3 was launched mid-build (~17:57, Map One's zm_tower_of_doom per the console); per the build script's ritual the generated sound/zone cache was cleared and the build re-run clean. SUPERSEDED AS THE TEST .ff by the Haven session's FULL BUILD OK 18:51 (tmp/haven/full2.log; .ff 18:49:31, FF 228,294,976 B), which carries this tree (verified: the 8 changed scripts / Lua in its ledger, the new stems in its loaded bank, deployed = repo, nothing synced after). UNPLAYED.
