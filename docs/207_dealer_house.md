# 207 — THE DEALER'S HOUSE: the Battle Arena's final fight

STATUS: v1 LANDED 2026-10-04 (source + gates + generated art/cues/voice). BUILT 12:04 (see "Build" at the end). UNPLAYED.

User (2026-10-04): *"We need to build a separate arena that is even better and slightly bigger than existing one.
This is the one players will get sent to on battle arena wave 10. The final fight. It starts off as player getting
sent into a small box with the Black Market as the only thing in the center of room. Then a cut scene will start where
the dealer starts talking to the players. And he ends up identifying himself as the evil mastermind etc. You can come
up with whatever lines. but the whole point is that he then teleports the players into the new battle arena and gets
the players down to one HP with the same effect that the evil dome gives. Same visual so its a callback and scary since
you have one health but you cant die. He talks a bit and then the boss fight starts. Implement all of this and the boss
fight will only be him in his two phases but we will continue enhancing after."* + *"you need to build two more rooms
for this"* + *"He lets you roll one last time and you get a very evil bad roll and he laughs like crazy. This is when
he teleports you into the final fight"*.

## 1. The experience, moment by moment

Level 10 of the Battle Arena (docs/185) no longer runs waves and the Keeper. The chamber on floor 40 charges as ever
(the banner reads BATTLE ARENA - THE FINAL FIGHT; the chamber's notice says the same), the tower is held, and the party
lands in:

**THE PARLOUR** — a 704-square, 320-tall box at (-8000, 8000) with the Black Market hut at its exact centre and
nothing else. The music stops. The hut lights (its own parts: the neon, the mask, the valve, the sparks). Every player
stands in a line before the counter. THE SCENE: the letterbox drops, the gun goes down, the feet are pinned (the card
panel's soft freeze — companions stop too), the view locks on the mask with a little room to breathe. Four lines from
the mask, 3D:

1. *Come in. Come in. You climbed a long way down... to stand in a room with nothing in it but me.*
2. *Every roll you ever made is in my ledger. Every card. Every spin. You thought the luck was yours. It was mine. It
   was always mine.* (the counter sparks under it)
3. *The tower didn't fall. I folded it. The sign in the sky, the domes, the voices in the walls... all of it was the
   house. All of it was me.*
4. *One more roll. On the house. Go on... I insist. Everyone gets one last roll.*

**THE LAST ROLL** — the bars lift and the counter prompts ONE LAST ROLL (its own trigger: `BLACK MARKET - the last roll
/ on the house - FREE`; the normal spin's two prompts stay dark). The first player to hold USE rolls for everyone; after
25 s he rolls for them (*Too slow. I'll roll for you.*). Everyone is frozen and every screen shows THE SAME reel (one
seed): the slam, the luck pour (the bar reads full — "on the house"), thirty tiles, the crawl, a STOPPED SHORT hang on a
LEGENDARY LUCKY CHARM with the jackpot's own heartbeat... and the fall onto a tile that is not on the wheel: **CURSED**
— a blood-red tile with his mask on it, HOUSE WINS / ALL YOUR HEALTH BUT ONE where the prize goes, a cursed banner
stamping in, red rays, shards, a dark red flash and the shake, his jackpot face in the curse's red. *CURSED! Oh, look
at that. The house wins. The house ALWAYS wins.* Then THE LAUGH (9.4 s, manic; the counter sparks and blasts, the room
shakes) over the cursed banner. The panel drops. *Now. Let me show you where the money goes.* — the teleporter's charge
rides the line and the party is sent to:

**THE HOUSE** — the final arena at (8000, -8000): 1920 square (the arena is 1664), 720 tall. THE PIT at z 0 with
THE DAIS at its centre (a 384-square top at z 96 on a solid block, a full-width flight of eight risers down every side
and the corners open to the pit — every side is a stair, so he walks up to anyone on it), THE RING at z 120 round the walls (an open ledge onto the pit, four pinwheel stairs), four pylons with lit
collars, four lit GATES in the pit walls (his entrances), the vented roof. Every level is on foot: no camp. The party
lands on the dais top, frozen, and the haven's CORRUPTED dome rises round them — the field model at twice its size,
its boot stutter, its dark hum, its red fx — and every screen takes the corrupted haven's red tint and darkness (the
haven HUD's own state: the callback). *You remember my domes. Breathe it in. I'm not taking your life. Only...
everything but the last of it.* THE DRAIN: ten cuts over six seconds, a red flicker and a bite each, the health held
on the line between them; at the end everyone is at ONE and held there. Nobody can die: a damage callback eats
everything while the shield holds and the health line is re-written every tick (stock regen cannot climb). *One. One
point of health. Hold on to it. I would.*

**THE FIGHT** — he rises through his portal at the gate farthest from the party and waits (held: no hunting, the idle
plays). *The account is open. Let's SETTLE it!* — under the line the dome breaks (the cleanse stutter, the guardians'
rise) and the darkness lifts; at its end the freeze ends, the shield drops, the readout reads THE FINAL FIGHT / THE
DEALER, the horn sounds, the boss track starts and the mood lights go red. He fights in his two states (docs/199:
the scythe float; at half health the mask cracks — *My FACE! Mm. You'll pay for that one.* — and he runs with the gun).
A player going down: *One more for the ledger.* His death: *A bigger mask... under this one... always... another.* —
and the level is won: the arena's own win (LEVEL CLEARED under THE FINAL FIGHT, the fanfare, every player a card in a
frozen world, the ride home from the house's dais to the top bay, THE BATTLE ARENA IS CONQUERED).

Health regen resumes from one when the fight starts (the user's "one health but you cant die" is the drain and the
talk; the fight is live).

## 2. The pieces

| Piece | Where |
|---|---|
| THE ROOMS (geometry, zones, seeds, probes, lights, the GENERATED data) | `tools/dealer_house_layout.js` -> `gen_tower_map.js` block 6zz -> `_tod_house_data.gsc` |
| THE FLOW (parlour, scene, last roll, laugh, send, dome, drain, fight, end) | `scripts/zm/zm_tod2_cybercity/_tod_house.gsc` |
| THE ARENA's branch (level 10 -> the house; the readout's HOUSE / DEALER flags; the ride home from `level.tod_arena_depart`) | `_tod_arena.gsc` (`TOD_ARENA_HOUSE`, `TOD_ARENA_HUD_HOUSE` 16, `TOD_ARENA_HUD_DEALER` 32) |
| THE COUNTER + THE RIGGED REEL (`shop_add`, `house_shop_begin/end`, `house_roll`, `house_roll_end`, the hold on the cycler and the voice watchers) | `_tod_shop.gsc` (`TOD_SPIN_CURSED_TILE` 60, `TOD_SPIN_CODE_CURSED` 9, `TOD_SPIN_CURSED_TEASE` 39) |
| THE CURSED LANDING on screen (`CURSED` table, `landCursed`, the cursed tile in `paintTile`) | `TodSpinReel.lua` |
| THE READOUT's two new lines | `TodArena.lua` (`FLAG_HOUSE`, `FLAG_DEALER`: THE FINAL FIGHT / THE DEALER) |
| THE DRAIN's flicker (`tod_house_cut`) | `TodHaven.lua` (red, only inside the corrupted state) |
| THE LETTERBOX kept alive (`tod_jump_cine 3` re-arms the watchdog) | `TodJumpCine.lua` |
| THE DEALER held while he talks (`level.tod_dealer_hold`) and his voice hooks (`level.tod_dealer_crack_fn` / `_death_fn`); the crown-hall test spawn OFF | `_tod_dealer_finale.gsc` |
| THE LINES (14, group `house`) | `tools/black_market_vo/lines.json` -> `generate.py` -> `pick.py` (wavs, `tod_shop.csv` rows, the GENERATED `_tod_shop_vo.gsc` length table) |
| THE CUES (cursed / drain / cut, GENERATED) | `tools/dealer_house/make_sounds.py` -> `sound_assets/tod/house/`, `sound/aliases/tod_house.csv`, the szc |
| THE ART (cursed tile / banner / mask icon, GENERATED from the legendary set + our glyph sheets) | `tools/dealer_house/make_spin_art.py` -> `source_data/tod_ui_images/_images/i_tod_spin_*_cursed.png`; review `art/dealer_house/review/spin_cursed.png` |
| THE READERS that must treat the rooms as "away" | `_tod_ambush` (legal + the player filter), `_tod_reach` (region_of), `_tod_atmosphere` (the music floor), `_tod_gauge` (the tier floor), `_tod_arena` (the fall guard) |
| THE ZONES | `zm_tod2_cybercity.gsc` (`house_parlour_zone`, `house_zone`: adjacent to nothing, enabled by the house) |

## 3. Rules paid for (and kept)

* **A gated path is consistent at every instant.** Everything above was staged in a scratch mirror of the gated trees,
  proven through the whole gate sweep there, and landed in one step (every anchor asserted, every file's own line
  endings kept).
* **The last roll is a protocol, not a prize.** The reel draws exactly like a bought spin until it lands (one seed to
  every player); the server never pays, never scraps, never touches a slot. The near-miss rule (never show a prize and
  take it back) is kept: the LEGENDARY it hangs on was never landed.
* **gsc_eval has no `switch`.** A pure function the gate runs (`line_is_2d`) is an `||` chain.
* **The letterbox's watchdog is 17 s.** A scene longer than that re-arms it with the `3` beat (`TOD_HOUSE_CINE_KEEP_SECS`
  8); the gate fails a keep-alive slower than the watchdog.
* **A terrace Havok can climb from every direction is not a floor to it.** The first dais was a pyramid of concentric
  12-high slabs; cod2map's navmesh gave it NO polygon above the pit (the 2026-10-04 build 1 navmesh gate): Havok merges
  a climbable terrace into the floor polygon it rises from (a 12-high slab vanishes into the floor, a 48-high one is its
  own island). A flight with OPEN sides is bordered by its drops and meshes — the arena's dais + spoke grammar — so the
  dais is a top on a block with a full-width flight per side and open corners, proved with cod2map on scratch variants
  (20 s a run) before the second build.
* **A DECK material on a trim is a floor nobody can reach.** `tod_cc_ruby` is a DECK to lint_tod_geometry (the dais
  ring walk-over): the house's seams, collars and gate bars wear `oxblood` (BLOCK). The lint's island logic is generic
  now (`ISLANDS`: arena / house / parlour, each flooded from its own floor, each gated at zero detached).
* **The drain never raises a player.** `drain_target` only ever lowers; stock regen cannot climb under the tick; a
  downed player is left to last stand.
* **Never strand the party.** A Dealer who cannot spawn after ten tries is logged (`DEALER_NOSHOW`) and the level is won
  without him; a house whose zones are missing refuses before anyone moves (the arena refunds and releases).
* **The tester kit's start level.** `TOD_ARENA_TEST_START_LEVEL` 10 under `TOD_TESTER_KIT`: a tester's first arena trip
  is the final fight (set it to 1 for the ten-level climb; it goes away with the kit).

## 4. Knobs (one per symptom)

`_tod_house.gsc`: `TOD_HOUSE_CINE_YAW` / `_PITCH` (the locked view's freedom), `TOD_HOUSE_ROLL_WAIT` (25 s before he
rolls for them), `TOD_HOUSE_DOME_SCALE` (2.0 x the haven's field), `TOD_HOUSE_DRAIN_SECS` / `_STEPS` (6 s, ten cuts),
`TOD_HOUSE_DOWN_VO_PCT`, `TOD_HOUSE_MOOD_IDX` (the glow colour), `TOD_HOUSE_LOG` (1: prints with dev OFF — ZERO before a
publish; build_map refuses -Publish while it is 1). `_tod_shop.gsc`: `TOD_SPIN_CURSED_TEASE` (what the reel hangs on).
`_tod_dealer_finale.gsc`: his health and the crack fraction (docs/199). The lines: `tools/black_market_vo/picks.json`
(the take per line; the laugh is take 2, 9.44 s), regenerate with `generate.py --group house`, ship with `pick.py`.

## 5. Gates

`tools/test_dealer_house.js` (211 checks, 25 mutants: the rooms generated + vented, the flow order, every undo in
release/end, every line shipped + rowed + timed, the arena's branch, the LOCKSTEP bits, the cursed reel, the wiring);
`make_spin_art.py --check`, `make_sounds.py --check`, `pick.py --check`; the arena / spin / pursuit / ambush / haven /
dealer gates and the Lua harnesses (`test_arena_hud`, `test_haven_hud`, `test_spin_reel`) carry the new checks;
`lint_tod_geometry` (both islands at zero detached), `lint_tod_navmesh` (the house's arrivals + gates + probes on one
component; the parlour's arrivals on mesh), `gen_lanes.js --check` (the sky fleet re-routed round both rooms).

Logs `[TOD_HOUSE]`: INIT / PARLOUR / CINE / LINE / ROLL / CURSED / LAUGH / SEND / HOUSE / DOME / CUT / ONE / SPAWN /
FIGHT / DOWN / CRACK / DEALER_DOWN / RELEASE / END; `[TOD_SHOP] HOUSE on/off`, `HOUSE_ROLL`, `HOUSE_ROLL_LAND`;
`[TOD_DEALER] HOLD`; `[TOD_ARENA] TEST_START_LEVEL`.

## 6. Not yet (the user: "we will continue enhancing after")

The fight now includes warned fixed-position Wunderwaffe shocks and six-round Dingo bursts with native two-hand
gun clips (docs/dealer_combat/README.md). Guarded FULL delivery is art/dealer_combat/build.json; native fight unplayed.
Adds are not implemented. (W2B, 2026-10-05: his black-soul aura, arrival rift, mask shatter, death and dissolve, his combat sounds
and his fight barks are docs/199 s5; the arena / house cues are AUTHORED now - `tools/dealer_sfx/make_sounds.py` writes
them BY NAME and `tools/battle_arena/authored_sounds.json` / `tools/dealer_house/authored_sounds.json` pin them, the two
generators' `--check` reading those pins instead of a fresh synthesis.) The parlour hut is the shop's own prop (the Dealer himself only appears in the
house). The cursed tile / banner / icon are generated from the legendary set; an authored set replaces them by name.
The dome over the dais is the haven's field model scaled, not a room-sized field.

## Build

FULL BUILD OK 12:04 (tmp/dealer_house/full2.log; build 2 - build 1 at 03:42 (full1.log) passed every gate, compiled + baked and DIED AT THE NAVMESH GATE: the dais, a pyramid of concentric 12-high slabs, had NO navmesh above the pit floor (Havok merges a terrace it can climb from every direction into the floor polygon it rises from; a 48-high slab is its own island), found with cod2map on scratch map variants (20 s a run) and fixed by the plus-shaped dais in tools/dealer_house_layout.js; the geometry self-test's PARITY case also needed the house's data file redirected in tools/lint_tod_geometry_parity.js): .ff 11:58:38, FF 230,443,904 B, a FRESH compile + bake (BSP 11:48:02, LED 246,277,485 B, the occlusion tome rebuilt, 695 tiles), NAVMESH GATE OK inside it (DEALER'S HOUSE: 4 arrivals + 4 gates + 25 surface probes in ONE component, the 4 parlour arrivals on mesh), the 8 known-waived linker lines only. Ran INSIDE it: GSC STRICT LINT OK 137, DEALER'S HOUSE OK 211 / 25 mutants, CURSED SPIN ART OK 3, HOUSE SOUNDS OK 3, BLACK MARKET VO OK 97, SPIN PASS 652, BATTLE ARENA OK 80, PURSUIT 158, AMBUSH 51, HAVEN GATE 453, HUD owner lifetimes 160, test_haven_hud (6 controls), ARENA HUD OK, every ledger check (JUMP TITLE / LUCKY / HAVEN 37 / WAR DAMAGE). VERIFIED after: the 11:58:38 ledger (all + english) carries scriptparsetree _tod_house.gsc + _tod_house_data.gsc + the 8 touched scripts, image i_tod_spin_tile_cursed / _banner_cursed / _ico_cursed (fresh .iwi 11:58:15), rawfile todspinreel / todarena / todhaven / todjumpcine, xmodel tod_haven_dome_dark + _flash, tod_dealer_body + _cracked, fx tod/haven/fx_tod_haven_corrupt + _boot, aitype spawner_tod_dealer; the fresh loaded bank (11:57:40, 167.6 MB) indexes all 17 house stems (3 cues + 14 lines); every landed input deployed = repo (41 files + tod_shop.csv / tod_house.csv at share/raw + the usermap, the szc), nothing synced after the .ff, no repo input edited after the 11:38:24 start.

SUPERSEDED AS THE TEST .ff by session -a4's haven v5 FULL BUILD OK 12:46 (tmp/haven_v5/full1.log; .ff 12:46:36, FF 233,280,000 B; a fresh compile + bake on the 12:32 repo tree = this house + -5e's Map One migration + haven v5), VERIFIED HERE read-only: its 12:46:36 ledger carries every house row (both scripts, the 8 touched scripts, the 3 cursed images, the 4 widgets, both dome models, both Dealer bodies, the corrupt + boot fx, the Dealer spawner), its 12:45:15 loaded bank (171.3 MB) all 17 house stems, NAVMESH GATE OK inside it with the house on one component, every house input deployed = repo, nothing synced after.

THEN by session -b6's Dealer's-gift FULL BUILD OK 13:34 (tmp/dealer_gift/full2.log; .ff 13:33:10, FF 233,681,472 B; the 12:43 bake reused; its _tod_shop.gsc gift lane + TodSpinReel gift tiles sit beside the house's pieces untouched), VERIFIED HERE the same way: every house row in its 13:33:10 ledger, all 17 house stems in its 13:32:18 bank, every house input deployed = repo, nothing synced after - THAT is the test .ff now.
