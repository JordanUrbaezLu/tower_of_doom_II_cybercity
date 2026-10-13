# 187 — Four rarities + THE PULL (card reveal v2)

STATUS: BUILT 2026-09-28 23:18:07 (-GscOnly, tmp/shop_spin/gsc3.log, FF 217,237,248 B); UNPLAYED.
Art still owed: the card back + rarity-neutral faces (section 6).
Prototype (the feel reference): https://claude.ai/artifact/UacYm8H4sVKmoMr3vrCz3d

User goals (2026-09-28): players in map 1 did not understand what Regular /
Super / Ultimate meant. Rarity must be obvious, rare pulls must feel huge, the
reveal must build anticipation like a CS:GO case ("they always go through the
animation but it's the anticipation"), and "the effects make it intuitive".

## 1. The rarity ladder (replaces Regular / Super / Ultimate / Dark)

| Id | Rarity    | Colour (RGB)     | Levels |
|----|-----------|------------------|--------|
| 0  | COMMON    | 233 238 245 white| +1     |
| 1  | RARE      |  58 168 255 blue | +2     |
| 2  | EPIC      | 181  92 255 purple| +3    |
| 3  | LEGENDARY | 255 194  61 gold | +4     |

- DARK UPGRADES ARE RETIRED WHOLE (lanes, 43 dark cards, dark aura, the
  `TOD_UPG_DARK_L` sentinel, pause "DARK:" rows, the spire's dark pool).
- THE WARDEN KING's dark-deal phase is REMOVED: max-out, then the fight.
- THE OVERCHARGE IS RETIRED (the secret 100..150 luck band, the zap art/sound,
  `guarantee_both_ultimate`, `TOD_LUCK_OVERMAX`). Luck tops out at 100.
- The headroom clamp stays: a card with fewer levels left than its rarity pays
  shows the rarity it can actually deliver (a Legendary with 2 levels of room
  presents as Rare).

## 2. Odds (per card, rolled independently) — user: "meet in the middle"

| Luck bar | Common | Rare | Epic | Legendary |
|----------|--------|------|------|-----------|
| Empty    | 56     | 27   | 13   | 4         |
| Full     | 36     | 36   | 20   | 8         |

Straight line between the two rows. Legendary roughly doubles at full luck
(user's pick). Guarantees:
- Full bar (100): one card is at least EPIC; that guaranteed card is LEGENDARY
  25% of the time (`GUAR_LEG_SHARE`, a knob — user said "can be legendary").
- Half bar (50): one card is at least RARE.
- First deal of the run: at least RARE (was Super).
- The S/A tier factor (`tier_rarity_factor`) still shrinks the upper slices.
- THE HOT STREAK (docs/201, 2026-10-02) multiplies the EPIC and LEGENDARY slices by 1.15 / 1.30 / 1.50
  (WARM / HEATING UP / ON FIRE) after the tier factor; COMMON pays for it. The guarantees ignore heat.

User set Legendary to 4% at an empty bar (2026-09-28, "legendary is too common"); the
removed share went to Common, so Rare and Epic are unchanged. Still ~35% more
levels per card than the old odds.

## 3. Card art: one face per upgrade, the rarity is drawn live

User's pick. Each upgrade gets ONE rarity-neutral image (title, picture,
description); the game draws the frame colour, the "EPIC +3" band, the glow
and the pips. Cuts the card set from ~237 images to ~65, lets the rarity frame
animate during the flip, and a rarity can never show on the wrong card.
Needs an art pack: neutral faces + the card back (+ optional frame pieces).

## 4. THE PULL — the reveal (auto, NOT skippable — user)

1. Deal: world dims, both BACKS slam down (identical black-chrome back with the
   tower sigil; nothing readable from it).
2. The climb, one card at a time: the back charges through the rungs
   WHITE -> BLUE -> PURPLE -> GOLD. Each rung: colour surge, sweep, rising tone,
   harder shake. Every rung ends in a HEARTBEAT hitch where it might stop, so
   the player never knows. Epic tints the screen edges purple; Legendary dims
   the world, gold vignette, screen shake.
3. A LADDER beside each card (COMMON +1 / RARE +2 / EPIC +3 / LEGENDARY +4)
   lights rung by rung — the teaching device, seen every deal.
4. The flip, scaled by rarity: Common a clean flip + click; Rare a blue
   shockwave; Epic rises, spins 1.5x, rays, shards, purple flash, chord;
   Legendary rises, spins 2.5x, gold god-rays that keep turning, white-gold
   flash, 28 shards, bass drop + shimmer, floating gold motes, pulsing halo.
5. A banner stamps the meaning: "EPIC / +3 LEVELS", then shrinks into the card.
6. The gained level pips light one at a time with a rising chime.
7. Pick: the other card shatters, the taken card flies to the HUD corner.

Prototype timings (ms, paused world): rung dwell 440/480/580/820 incl. a 190
hitch, flip 280/360/620/1050, post-land beat 260/400/650/1000. Totals per card
~0.8 s Common, ~1.5 s Rare, ~2.4 s Epic, ~3.5 s Legendary. Co-op altar (live
world) keeps the existing x0.5 (`TOD_REVEAL_LIVE_SCALE`).

OPEN (toggles in the prototype, user to decide):
- near-misses (a card flickers toward the next rung, then settles) — off by default.
  IMPLEMENTED 2026-10-02 as THE REACH (SO CLOSE or BREAK THROUGH, from the card's real result) with the hot
  streak (warm backs, heated EPIC/LEGENDARY odds): docs/201 section 10.
- teammate alert ("<NAME> PULLED A LEGENDARY") — proposed Legendary only

## 5. Engine plan (zero new clientfield bits)

- The server DRIVES THE CLIMB: `reveal_slot` pushes the slot's rarity field
  0 -> 1 -> 2 -> 3 with a real wait per rung, then the domain. The Lua already
  re-enters on every rarity change, so each push = one rung; the active slot is
  derivable (A while AD == 0, then B while BD == 0). No client clock, and the
  x0.5 station scale applies automatically.
- Rarity fields (2 bits) carry 0..3 = Common..Legendary. "No second card" moves
  off BR == 0 onto `todMagBonus` (1 bit, dead since 2026-08-20).
- Lua tween lanes proven in-tree are alpha + rect only; a 3D spin is not
  available — the in-game flip is a rect squash/expand (back narrows to the
  spine, face opens), rotation/rays pending a native test of setZRot.
- Knock-on edits: `roll_rarity`, `guarantee_rarity`, rarity locks
  (Deadshot / Mystical Hands), `o.levels`, card sting/aura sounds, pause +
  scoreboard rarity text, both armory pages, patch-notes wording, lint_tod_assets
  (rarity list), the 3/6/9 card rule (a +4 can cross two steps).

## 6. What shipped, and what is still owed

- Server: `_tod_upgrades.gsc` (odds, guarantees, labels, dark gate 0, King dark phase gone),
  `_tod_luck.gsc` (overcharge gone), `_tod_upgrade_ui.gsc` (THE PULL timeline, `todUpgSolo`,
  Legendary aura + teammate announce), `_tod_spire.gsc` (no dark phase / latch).
- Client: NEW `ui/uieditor/widgets/HUD/AetheriumWidgets/TodPull.lua` (zoned in the .zone);
  `tod_upgrade.lua` decodes the wire, hands every paint to `CoD.TodPull.Render`, registers
  one face per upgrade. The old v14.52 socket reveal is the fallback when TodPull is absent.
- The in-game flip is a squash-and-open (only alpha + rect tweens are proven in LUI); no 3D
  spin, rays or floating motes yet. Card back = panel placeholder until `i_tod_card_back`.
- Sounds are synthesized placeholders (`tod_pull_*`); swap by filename.
- OWED: the art pack (card back + ~27 rarity-neutral faces, then the band/pip COVERS in
  TodPull.lua go); the has_dark() lane removal pass; the near-miss and teammate-alert calls.

## 7. Dev CARD TEST bench (testing the reveal)

With `level.tod_dev` on, a crafting table in the crown hall (between the uplink dais
and the sanctuary steps) deals a test panel on every press: COMMON+RARE, EPIC+LEGENDARY,
LEGENDARY+LEGENDARY, RARE+EPIC, a lone LEGENDARY, COMMON+COMMON, then random. Levels are
ignored (the maxed dev loadout still gets cards) and the pick is never applied.
`_tod_upgrades.gsc` `dev_card_test_*`, logs `[TOD_CARD_TEST]`.

## 8. Pass 2 (2026-09-29): the game matches the prototype

User after playing the first build: "Looks pretty bland without UI", "doesn't look like the
artifact", "change our card design in general so that it works with this new system ... all
upgrade cards for archer first", "Make sure the HUD doesnt show when cards are getting pulled".

- THE HUD VEIL: `TodHudVeil.lua` (`CoD.TodHudVeil.Set( key, on )`). The card panel owns
  "cards", the Item Shop wheel "spin" (session 9c). AetheriumHud's two absolute hide writers
  became ONE rule (scoreboard OR pause OR veil); tod_upgrade's HUD pieces live in a veiled
  `HudOnly` container. The bold centre messages stay (a teammate's LEGENDARY alert).
- EFFECTS ARE SPRITES, generated white by `tools/card_pull/install_card_art.py` and tinted:
  card glow, god rays (8-fold, turn 45 deg per step via zRot - a non-interpolating engine
  shows still rays, never a jump), diamond shards, ring, radial flash, edge glow, sweep,
  band pill, pips, ladder gems, rising motes (LEGENDARY).
- CARD V2 (docs/191): illustration -> body -> rarity frame -> crest -> live title, two short
  lines (`face` in the DOMAIN row; the typeface draws A-Z 0-9 - ' . / + only), band, pips.
  Drawn only when the layers are installed (`CoD.TodCardArt`, GENERATED); else the old card.
- BUG found by rendering: the typeface has "+" and "/" only in its DIGIT set, so every
  "EPIC +3" / "COMMON +1" / "LV3 / 6 / 9" measured -1 and hid. TodPull's `Pick` routes them.
- An unclimbed back is a dim steel, never the COMMON white (read as "stayed common").
- SEE IT WITHOUT THE GAME: `python tools/ui_mockup/render_pull.py [--v2] [--deal 4:4,3:2]`
  runs the real Lua under a TIMED mock (`mock_lui_anim.lua`) on the server's exact beat
  schedule and writes frames, a contact sheet and a GIF to tmp/ui_mockup/pull/.
- Gates: `tools/test_card_pull.lua` (66 checks incl. the veil and v2), and a build step
  `card_pull --check` (images / GDT / zone block / manifest in step).
