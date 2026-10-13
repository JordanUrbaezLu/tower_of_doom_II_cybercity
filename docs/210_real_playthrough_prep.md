# 210 — THE FIRST REAL PLAYTHROUGH: dev and god mode off, flows and balance reviewed

STATUS: LANDED 2026-10-04 15:10 (source + gates), pass 2 20:30. BUILT: FULL BUILD OK 15:25; pass 2 built 21:36 (see "Build" at the end). UNPLAYED.

User (2026-10-04): *"Lets review this map entirely and turn off dev and god mode and prep for an actually play
through, Review the flows and balancing to see what need to be adjusted and we have been testing in dev and god
mode the entire time so we may have missed a few things that need to be adjusted here for a real game."*

Every playtest of TOD II so far ran with five test lanes armed: dev mode (100,000 points every 2 s AND every tower
door opened free at spawn), god mode (health floors at 1, never a down), the maxed tier-3 loadout with every card
capped, unlimited ability cooldowns, and every class gun held at once. The crown's tester kit also sent the FIRST
Battle Arena trip straight to level 10 (the Dealer). So the money curve, the door ladder, the tier-1 loadout, the
real cooldowns, every damage path and the arena's climb have never been played.

## 1. What was switched off

| Switch | Was | Now | What it did |
|---|---|---|---|
| `level.tod_dev` | true | false | money loop, every tower door open, crown shop lit before power, card-test table, camo browser, dev prints |
| `level.tod_god` | true | false | health floored at 1 (damage landed, downs never happened) |
| `level.tod_dev_maxed` | true | false | tier 3 + every card at its cap on spawn |
| `level.tod_dev_unlimited_offhand` | true | false | no cooldown / charge on any lethal or tactical |
| `level.tod_dev_all_guns` | true | false | all three tiers' guns of the class at once |
| `TOD_TESTER_KIT` (`_tod_tester.gsh`) | 1 | 0 | the crown's class terminal, AND the arena's first trip at level 10 |
| `TOD_PARTNER_TEST_BENCHES` (`_tod_partners.gsc`) | 1 | 0 | four free companion benches in the crown hall |

`build_map.ps1 -Publish` now finds nothing armed. To make a testers' build again, set `TOD_TESTER_KIT` back to 1.

**THE LOGS STAY ON.** About 60 feature loggers were gated on `tod_dev` alone, so dev off would have left the
playthrough with no evidence. NEW `level.tod_diag = true` (entry script, beside the dev flags) lets those
console-only loggers print: `[TOD_ARENA]`, `[TOD_HAVEN]`, `[TOD_AMBUSH]`, `[TOD_KIT]`, `[TOD_DROP]`,
`[TOD_ELITES]`, `[TOD_HUNT]`, `[TOD_RECALL]`, `[TOD_PULL]`, `[TOD_LUCK]` and the rest. Each one was checked to
print only to the console (inside a `/# #/` dev block) and to call nothing else. It changes no value, shows
nothing on screen, and the publish gate deliberately does not read it. Inline dev prints and the elite AI
recorder (`dev_ai_watch`) stay dev-only.

## 2. What was adjusted (things that broke or got worse once the crutches were gone)

1. **The crown's three doors are flat in co-op** (`_tod_doors.gsc door_price_for`). The 5000 hall gate is the
   only way out of the crown and BO3 cannot pool points, so one player paid it party-scaled: 6447 duo, 9211
   trio, 11974 quad, while each player's income per round is about 0.6x solo (the round grows ~2.4x for four
   players and splits four ways). The two 1500 hallway doors (Power Room, Teleporter) follow the same rule.
   Solo is unchanged; every tower door keeps its scaling. The hint and the charge both read the new function,
   so the sign and the price agree.
2. **The Breacher's Mozambique carries 30 magazines, not 20** (`tools/gen_tod_twins.js` `reserveMult: 1.5` on
   the tier-1 row, regenerated `source_data/tod_weapon_twins.gdt`): 63 -> 93 shells. The crown has no ammo
   crate (retired on purpose), the Breacher's C4 and Cluster are card-earned (level 0 = an empty slot), and the
   first crate below the crown is inside the floor-40 haven, so a real tier-1 Breacher had 63 shells for the
   6500 out of the crown and ten floors after it. The map uses stock powerup drops, so a Max Ammo turns up in
   the crown in roughly four runs of ten. DPS is untouched (the sustained pin still matches 1235 / 2229). The
   reserve is DERIVED by the generator (the retired gun's time on the trigger), so the multiplier now scales
   that pin; the 870 and the Peacekeeper are unchanged. `tools/test_starter_weapons.js` pins 30. GDT change =
   FULL build.
3. **A downed teammate no longer feeds the crown's hunter ramp** (`_tod_fall.gsc player_in_hall`). The ramp
   (Doppelghast / Mangler from 90 s after the alarm) runs "while someone is in the hall". A downed player
   counted, so the ramp kept spawning hunters on that player after the rest of the party had jumped.
4. **The companion nudge says where** (`_tod_shop.gsc gift_nudge`): "A FREE AI COMPANION WAITS AT THE BLACK
   MARKET IN THE CROWN HALL". The only Black Market lights at the power, when the party is in the power room or
   on the balcony beside the one-way jump pad, and there is no other counter until the ground floor (the base
   teleporter back to the crown). Dev mode lit it from the first second, so the gift was always in hand.

**Pass 2 (20:30, after the full review finished):**

5. **The Dealer no longer stacks the arena's level-10 hit multiplier** (`_tod_arena.gsc`, the house branch).
   The house set level 10's x2.35 and his own x1.25 applied on top: 45 x 2.35 x 1.25 = 131 a swipe, two hits
   down through Juggernog, in a fight that starts at one health. He is the house's only attacker, so his own
   x1.25 is now the whole number: 56 a swipe, three hits at base health, five with Juggernog.
6. **The Battle Arena's difficulty is static per level, as you described it** (2026-10-03: "rounds dont count in
   there and its a static difficulty of progression through the battle arena levels"). Arena enemies used to
   take the TOWER round's health at the moment of entry, so the same level was about twice as hard entered ten
   rounds later, and the Dealer's 60 round-zombie healths ran away with the round (round 40: 98,000 a player).
   Now each level fights at one fixed round: round 10 for level 1, two more per level, level 9 at round 26, the
   Dealer at round 28 (`TOD_ARENA_HP_ROUND_BASE` / `_STEP`, published as `level.tod_arena_hp_round`, which
   `_tod_power_scale::track_rounds` holds while a fight runs - zombies, elites, the Dealer and every ability that
   hits in round-zombie units agree). The per-level health and hit multipliers still apply on top.
7. **An arena trip no longer deletes a haven's guardians** (`_tod_arena.gsc hold_tower`). The stairs pass inside
   every haven's wake band, so walking past a haven wakes its guardians; stepping into the arena deleted them,
   their "death" counted them down, and the haven cleansed for free (+500 each). They now stay in their field.

## 3. The review: what a real run looks like (solo unless noted; "~" = estimate)

### The crown (spawn -> the jump pad)
- Start money 500. Escape = the 5000 gate + the 1500 Power Room door = 6500, then Quick Revive 500 on the
  balcony. A kill pays ~60-130 (stock: 10 a non-lethal hit, 50 + location on the kill, 120 a melee kill); a
  hunter pays 500 to its killer. ~86 kills, or fewer with hunter purses: about 2-3 minutes of play.
- Round sizes 7 / 9 / 15 / 21 / 27, every zombie sprinting from round 1, the crown's spawn delay about half of
  stock (`TOD_SPAWN_MULT` 0.70 x the Fall's 0.7), 30-38% of spawns climbing out round a player (THE AMBUSH).
- THE RAMP: the first Doppelghast 90 s after the alarm, a Mangler at 120 s, then the gap shrinks to 5 s; the
  cap starts at 2 and grows one per two spawned (max 10). A player who leaves in ~3 minutes meets ~2-4.
- Health: 150 at base, no Juggernog anywhere in the crown, about three zombie hits to go down. Hunters swing
  for ~35.
- **Solo has one life in the crown.** Quick Revive is on the balcony, behind the bridge door that opens with the
  power (your 2026-09-25 call: "the jump pad and Quick Revive must not work until the power is on"). Any down
  before the balcony ends a solo run. NOT CHANGED - the options are below.
- The Black Market and the crown Pack-a-Punch (5000, live from the alarm) compete with the 6500 escape.

### The descent (floors 50 -> 1)
- 27 paid doors, 750 at the top rising to 3000; the whole ladder is 58,290 solo, a third of the old climb. The
  other 24 transitions are free broken drops, and the catch decks zero their fall damage (`broken_fall_guard`).
- Perks live in the four havens (two machines each, reshuffled every few rounds). Haven machines (perks, crate,
  Pack-a-Punch) work while the dome is still corrupted; only the teleporter pad and the arena gate wait for
  the guardians. The first crate below the crown is in the floor-40 haven.
- Guardians: 40 / 30 = 1 Doppelghast + 2 Manglers, 20 = 2 + 2, 10 = 2 + 3 (+1 Doppelghast for 3-4 players),
  at 8 / 6 round-zombie healths. The cleanse pays every player 500.
- Co-op respawns land at the unlocked respawn group nearest a living teammate (the terrace, a haven, the
  plaza), never past an unbought door.
- Tier 2 needs floor 40 AND the class gun packed; tier 3 needs floor 20.

### The Battle Arena and the Dealer
- Free entry from the floor-40 chamber once that haven is taken. Now opens at level 1 (it opened at 10 with the
  tester kit). Per level: 12 + 3 zombies a wave (x1.6 for "the horde" set), 3 waves, enemy health
  x(1 + 0.25 per level) and hits x(1 + 0.15 per level), elites from wave 1 on level 3+.
- Level 10 = the Dealer's House. The drain to one health runs under an invulnerability shield that is
  released in one place; nobody can be left immortal. He has a melee swipe only (x1.25), starts at the far
  gate, and the party regenerates before he arrives. His health is 60 round-zombie healths per player.
- No invulnerability leaks anywhere: every enable (spin, world pause, house, terminal) has a matching release
  that also checks the other holders.

### Class kits at tier 1 with no cards
| Class | From spawn | Earned by a card |
|---|---|---|
| Archer | the Bow (no reserve limit), the grapple (12 s) | the Retriever (lethal), grapple range + landing buff |
| Breacher | the Mozambique only | C4 (lethal), Cluster (tactical) - level 0 is an empty slot |
| Warrior | the fists, Bash (12 s, 1 charge) | Gravity Smash (tier 3 only, kill-charged) |
| Necromancer | the skull (a 100-point meter: the beam costs 7 a second, it refills 14 a second when idle), summons, the Soul Pulse (kill-charged) | the Invisibility Cloak |

The Breacher is the only class with no ability at all until a card lands. Your call (2026-09-26: "C4 and
CLUSTER are EARNED"); not changed.

### The numbers (the full review, solo, body shots; "~" = estimate)

Zombie health is map 1's curve / 10. Seconds to kill one zombie at each tier's sustained damage:

| Round | Health | T1 | T1 packed | T2 | T2 packed | T3 | T3 packed |
|---|---|---|---|---|---|---|---|
| 10 | 94 | 0.8 | 0.4 | 0.4 | 0.2 | 0.3 | 0.2 |
| 20 | 243 | 2.0 | 1.1 | 1.1 | 0.6 | 0.7 | 0.4 |
| 30 | 630 | 5.1 | 2.8 | 2.9 | 1.6 | 1.8 | 1.0 |
| 40 | 1,634 | 13 | 7.3 | 7.5 | 4.2 | 4.6 | 2.6 |

Hits to go down (150 health at base, 250 with Juggernog):

| Source | Damage | Base | Juggernog |
|---|---|---|---|
| Zombie swipe | 45 | 4 | 6 |
| Doppelghast / Mangler melee | 35 | 5 | 8 |
| Arena level 5 / level 9 zombie | 72 / 99 | 3 / 2 | 4 / 3 |
| The Dealer, before pass 2 | 131 | 2 | 2 |
| The Dealer, now | 56 | 3 | 5 |

Cards: a deal at the class draft and every 4th round after it (2 cards, pick 1), plus one per arena level won
and one per altar buy (3000, 5 a station). ~9 card levels by round 8, ~15 by 16, ~20 by 24. Any one named card
is offered in 22% of deals (25% for the Warrior): about half the time by round 8.

Perks: Quick Revive 500 solo / 1500 co-op on the crown balcony only; the other eight are shuffled over the
eight haven pads (two each on floors 40 / 30 / 20 / 10) and move every 4 rounds. Juggernog 2500, Speed Cola
3000, Stamin-Up 2000, Double Tap 3500, Widow's Wine 4000, PhD 2000, Death Perception 2000, Wisp Tea 3000.

## 4. Left for you to decide (not changed), most important first

1. **Solo Quick Revive is one life for the whole descent.** Its only machine is pinned on the crown balcony,
   and the crown seals when the party jumps. A solo player who self-revives once cannot buy it again until the
   ground floor and the base teleporter. Only a random free perk bottle (10% from elites) can return it.
   Options: let a cleansed haven hand a solo player Quick Revive back (the old spire's "a won trial returns the
   solo life"), or give Quick Revive a pad in the first haven. Also: solo has one life in the crown itself
   (Quick Revive waits for the power, your 2026-09-25 call).
2. **There is no ending.** The parked finale is unreachable. The Dealer's death is an ordinary arena win:
   cards, the ride home, "THE BATTLE ARENA IS CONQUERED", and the run goes on until the party wipes. Reaching
   the ground floor triggers nothing. Option: end the run with the existing escape screen when the Dealer dies.
3. **The Black Market exists only in the crown.** It lights at the power and is the only counter until the
   ground floor, so companion spins (2500) compete with the 6500 escape and stop at the jump. The free
   companion must be taken before the jump. Option: light a counter in the top bay or the havens.
4. **The Rampage switch exists only on the crown balcony**, so it cannot be flipped after the jump, though you
   asked for it to be toggleable all game (v19.0).
5. **No perk before floor 40.** Juggernog lands in the floor-40 haven only about a quarter of the time; the
   worst case is floor 10, and a reshuffle can move it to a haven already passed. Option: pin Juggernog in the
   floor-40 haven.
6. **The Breacher's card dependency.** C4 and Cluster are card-earned, and two more of the Breacher's nine cards
   (Explosive Fusion, Adrenaline) do nothing without them. About a third of Breachers still have neither by
   round 7. Options: gate those two cards on C4 or Cluster, and/or make C4 or Cluster always offered in the
   Breacher's first deal (that one would bend the "no weighted cards" rule).
7. **Arena trips always ride home to the top bay**, and the top bay has no pad to floor 40, so every one of the
   ten levels is followed by a ten-floor walk back to the arena gate. Option: ride home to the floor-40 haven.
8. **Real cooldowns nobody has felt:** the riot shield recharges in 240 s at level 1 (15 s in dev mode), the
   cloak lasts 3.25 s every 57 s, C4 / Cluster refill once a round, and the Necromancer's bind takes 7.2 s at
   level 0 (your 2026-09-26 number; you tested it with Summoning Power maxed, where it is 2.6 s).
9. **The Soul Pulse in co-op** needs half of the whole round's zombies but counts only your own kills: 120 of
   your kills at round 20 with four players. That follows your "factor in co-op"; the knob is
   `TOD_BOMB_ROUND_PCT`.
10. **Arena hits from level 6 down a player without Juggernog in two** (78-99 a hit). The knob is
    `TOD_ARENA_DMG_STEP` 0.15.
11. **The crown's pace.** Full sprint from round 1, half the stock spawn delay and the ambush are hectic by
    design. If the first real run is too much, the lever is `TOD_FALL_SPAWN_MULT` (0.7 -> 0.85 or 1.0) in
    `_tod_endless_rounds.gsc`, before touching the ramp. The ramp grows with kills, not time.
12. **Smaller things:** the crown's 1500 Teleporter room is a dead end until the ground floor; the jump pad
    fires on contact, one way; the Dealer fight starts at one health (your design, he starts at the far gate);
    two Undercity door prompts name the room you are standing in; SUMMONER MASTER level 1 is +4 health.

## 5. What to read in your log after the run

`[TOD_FALL]` (alarm, gate, power, RAMP, seal), `[TOD_ELITES]`, `[TOD_DOORS]`/`[TOD_DROP]`, `[TOD_SHOP] GIFT_*`,
`[TOD_JUMPPAD]`, `[TOD_HAVEN]`, `[TOD_ARENA]`, `[TOD_HOUSE]`, `[TOD_DEALER]`, `[TOD_PULL]` (cards),
`[TOD_LUCK]`, `[TOD_KIT]` (C4 / Cluster / Bash refusals say `locked_no_card`). Archive the console with
`tools/capture_ai_logs.ps1` before the next launch.

## 6. The first real run (2026-10-04 22:33, solo Breacher, the 21:36 build)

Log archived at `tmp/elite_tracking/runs/20261004_224719_637_611a184a/console_mp.log` (13 minutes, zero script errors;
every `[TOD_*]` feature log printed with dev mode off, so `level.tod_diag` works). Times are from the match start.

| When | What |
|---|---|
| 1:26 | class draft + round-1 card done; the hall waits for the alarm |
| 1:50 / 2:00 | alarm pulled / zombies released |
| 3:27 | the ramp's only hunter (a Doppelghast, 295 health) |
| 3:50 | the 5000 gate bought, round 6 (1:50 after the zombies came) |
| 4:04 | power on, round 7; 4:14 the free-companion nudge |
| 4:52 / 5:07 | the jump (12.1 s first-flight scene) / the crown sealed, round 8 |
| 5:04 - 9:08 | floors 50 -> 40: five broken drops, every landing at full health; the floor-40 guardians woke 7:48 (round 12), cleared 9:08 (round 14), +500 |
| ~10:00 | Juggernog bought (250 health at the next landing) |
| 11:28 / 11:36 | the floor-30 guardians wake (round 16) / the player walks into the corrupted dome |
| 11:41 | all three guardians dead within five seconds of each other; the game ends 0.35 s after the last |

What it says: the crown took three minutes, as estimated, and the ramp barely mattered (one hunter). The free companion
was never taken: the nudge fired, the player jumped without going back to the hall, and there is no second chance
until the ground floor (item 3 of section 4). The second haven was the killer at round 16 with Juggernog and no Quick
Revive self-revive. The log cannot say WHAT downed the player: nothing in the map logs a down. Suggested next
diagnostic: one `[TOD_DOWN]` line per down (attacker kind, damage, health before, Quick Revive held, haven state).

## 7. The second real run (2026-10-05 17:33, the 15:10 build: a Necromancer game, then a Warrior game)

Log archived at `tmp/elite_tracking/runs/20261005_175405_950_4cc72ed2/console_mp.log`. What the user reported, what
the log showed, and what changed (CHANGELOG 2026-10-05 18:29 and the entry after it):

| The user said | The log showed | Change |
|---|---|---|
| Doppelghasts "a bit too slow" | walk 1.0 since the first run | walk 1.25, sprint bursts every 4.75-8 s for 1.15-1.95 s |
| Manglers "dont shoot their blast enough" | 14 cannon shots; 160 RETARGET lines, one every 250 ms: the stock Raz target service writes the companion into the Mangler's target field, and the attack loop skipped its cannon while it held the companion | cannon 2.5 s after it starts attacking, then every 2.5 s, out to 1100 u; the Mangler keeps its own pick (`tod_hunt_player`) |
| the dark dome should raise "as many elites as players" | the per-floor roster | one guardian per player: 1D / 1D 1M / 1D 2M / 2D 2M |
| the bind "sticks to the floor and then freezes" | 9 holds, 2 conversions; most binds ended "lost" 5.5-6.9 s into 7.2 | one play of the lift + an in-air hold; a lost bind says why; a zombie being bound is off limits to the player's thralls and companions |
| the punch lunge causes "screen issues" | lunge reach 100 | no lunge; a punch the engine missed takes the first zombie in its cone (all 57 punches swept nothing: the cone's budget was the CLEAVE card's alone) |
| the R.A.P.S. was "almost like teleporting everywhere" and should hit by "running them over or touching them" | ~885 u/s; 24 charge / orbit flips under a second apart; only the 5 s blast ever hurt anything; every broken-drop jump fell to a traversal handler no script registers (session -13) | it locks one zombie, rolls slower (circling ~395 u/s, ramming ~560 u/s), hits whatever it touches and throws an ordinary zombie it kills; -13 registers the drop traversal |
| the Necromancer's limited, recharging meter: "I like this concept" | 10 empties, none of them heard | kept as is; a refused cue when it empties and when fire is pressed while it refills |

BATCH 1 (the elites, the in-air bind hold, no punch lunge) is BUILT in -ed's FULL BUILD OK 18:49:13 (tmp/playtest_1004/full2.log; .ff 18:47:20, FF 214,008,128 B), verified by ledger rows, the deployed weapon GDT and deployed == repo. BATCH 2 (the R.A.P.S., the Mangler's own target, the bound zombie left alone, the punch radius, the meter cue) landed 18:50:49 and is BUILT in session -13's -GscOnly BUILD OK 19:47 (tmp/logtriage/gsc1.log; .ff 19:45:08, FF 213,293,632 B) with -13's drop-traversal fix, verified the same way. Both UNPLAYED.

## Build

FULL BUILD OK 15:25:23 (tmp/real_playthrough/full1.log; started 15:09:40): .ff 15:23:22, FF 233,682,752 B; geom_key REUSED the 12:43 bake (BSP 12:40:38, LED 246,277,485 B), NAVMESH GATE OK on the reused mesh, a fresh occlusion tome (695 tiles), the 8 known-waived linker lines only, no material on a missing techsetdef, loaded bank 172,801,536 B (= the last good build), streamed 313,845,760 B. Before it, tools/run_build_gates.py ran 125 gates on the repo with one failure, fixed: tools/test_ambush.js pinned the old dev_log gate text and now also accepts the tod_diag form. VERIFIED: deployed scripts / ui / zone_source = repo, nothing synced after the .ff, no repo input edited after the build start, deployed source_data/tod_weapon_twins.gdt = repo (Mozambique 30 magazines); the ledger carries scriptparsetree for every touched script and weapon cc_mozambique_e0..e3 + _up. Peers -13 (asset audit; the Mage retirement and a Map 1 purge come next) and -a2 held their edits during it. UNPLAYED.

PASS 2 (20:30: fixes 5-7, `_tod_arena.gsc`, `_tod_power_scale.gsc`, `tools/test_dealer_house.js`): BUILT in session -13's FULL BUILD OK (tmp/mage_retire/full1.log, the Mage retirement; .ff 21:36:10, 230,164,608 B; geom_key reused the 12:43 bake), which carried these three files as they are in the repo: DEALER'S HOUSE OK 217 / 28 mutants and BATTLE ARENA OK 80 ran inside it; VERIFIED here read-only: scriptparsetree _tod_arena.gsc + _tod_power_scale.gsc in its ledger, both deployed = repo, the tod_arena_hp_round line and the guardian skip in the deployed scripts; every pass-1 change survived the merge (no armed dev flag, level.tod_diag, door_price_for, the downed-player skip, the gift text, TOD_TESTER_KIT 0, TOD_PARTNER_TEST_BENCHES 0, deployed Mozambique maxAmmo 30). -13's next FULL (asset batch 1) will supersede it as the test .ff. UNPLAYED.
