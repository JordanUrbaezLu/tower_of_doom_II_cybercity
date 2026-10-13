# 209 — THE DEALER'S GIFT: the Black Market gives you your AI companion

STATUS: LANDED 2026-10-04 (source + gates + generated art + voice). BUILD: see "Build" at the end. UNPLAYED.

User (2026-10-04): *"This concept of finding your parts etc is a bit much to get into the black market situation. I
think he should gift you a random AI companion on first use that doesnt use up your luck. Then you can continue to
upgrade. So we need to implement this in the black market system and make it easy for the player experience."*

Why it was "a bit much": since The Fall (docs/160) the party spawns in the crown and the Black Market is in the crown
hall, but a companion needed two parts from beside the Vault spawn and a bench in a workshop wing (docs/159) — both at
the BOTTOM of the tower, the run's end. In practice nobody could ever spin the Black Market (it refused anyone without
a companion), and no archived run had ever spawned a companion outside the crown TEST benches.

## 1. The experience, moment by moment

**The nudge.** Eight seconds after a counter first lights (the power coming on; dev: the start), every player with no
companion reads `A FREE AI COMPANION WAITS AT THE BLACK MARKET` (once per player; a card deal on screen goes first).

**The walk-up.** The lit counter shows a companion-less player its OWN prompt — `BLACK MARKET` / `A FREE AI COMPANION`
/ `NO POINTS OR LUCK - ON THE HOUSE` / `HOLD [key] TO TAKE` (no price row, no lock) — and the Dealer offers it as he
arrives (two new lines, no chance roll, a 20 s cooldown so pacing at the edge never repeats it):
*"Empty-handed? Down here? Come closer... the first one is on the house."* /
*"Nobody walks this tower alone. This city was full of little friends, once... I kept a few."*

**The hold.** Exactly like a spin: frozen, untargetable, unhurtable, the HUD veiled. The machine slams in — but no coin
drops and NOTHING POURS: the LUCK box keeps his bar exactly where it is, and where the odds would be the panel says
`THE DEALER'S GIFT - ON THE HOUSE` / `YOUR LUCK STAYS YOURS`. Under it, THE POOL: four boxes, the four companions
(portrait, name, COMPANION). The Dealer: *"On the house. Keep your luck. You'll need it."* /
*"Every customer needs a friend. Let's see which one... chooses you."*

**The reel.** Thirty companion tiles (a cyan COMPANION tile with the robot's portrait in its window) rush past the
needle on the spin's own cubic slow-down, crawling to 450 ms a tile (a spin crawls to 700): ~4.6 s. The ticks, the
lever, the five climbing crawl notes, the needle kicks, the rail lights and the Dealer leaning in are the spin's.

**The hit.** The tile flares cyan, `ON THE HOUSE` stamps in, rays, a ring, shards and the screen-edge glow (an EPIC-sized
celebration in the companion's colour), the stop clunk and the reveal sting; the Dealer GRINS; the right window that
waited empty PUNCHES in the companion's portrait with a cyan flash and its name; under the banner its name
(`CIVIL PROTECTOR`), what it does (`A RIFLEMAN THAT FIGHTS BESIDE YOU` / `A HOVERING GUNSHIP - FAST TRIGGER` /
`A ROLLING BOMB THAT BLASTS CROWDS` / `A TRACKED TURRET - SHREDS UP CLOSE`) and `IT FOLLOWS YOU NOW`; THE POOL gives way
to ITS three item slots, each saying `SPIN TO FILL` — what this counter is for next time. The Dealer's word waits for
his reel line to finish (it is never dropped by the one-voice lane): *"There. Yours now. Feed it well... and come back
when it's hungry."* / *"Oh, it LIKES you! Mm. Don't make it regret that."* (the occasional manic crack).

**The close.** After 3.2 s the panel drops and control returns (the spin's exit grace). The companion is his from the
moment the reel showed it; it deploys on the next manager tick, and EVERY companion arrival now MATERIALISES with the
teleporter's own arrival (the kino beam, the bright discharge + release field, the derez and the warp — the look a
recalled player gets), so the gift lands beside him in the world as the screen closes. Its HUD bar comes up
(`TALON - DEPLOYING` -> `TALON`), the pause menu / scoreboard AI COMPANION row names it.

**The next visit.** He has a companion, so the counter shows him the BUY prompt — spins for its items, as before
(docs/188): luck spent, 2500 points.

**Co-op.** Every player gets his own gift. The pick is random, but the Dealer hands out a companion nobody else in the
party holds while one is left (four players, four different companions); with all four taken, any.

## 2. What changed

| Before (docs/159) | Now |
|---|---|
| 8 part pickups beside the Vault spawn (8 hint strings) | gone |
| 4 workshop benches: build (3 s hold) then equip, swap (4 hint strings) | the 4 crafting tables stay as SET DRESSING (their collision clips are cut into the map; a clip with no table is an invisible wall) — no prompt, no scale model |
| Black Market without a companion: a LOCKED "companion required / Build one at a partner bench" card; holding USE got "Equip a companion first" + a refusal line | the GIFT prompt; holding USE runs the gift |
| 2 dealer refusal lines (`tod_spin_vo_no_companion_1/2`: "build your little friend first") | retired whole (lines.json, wavs, alias rows, length table); 6 gift lines in |
| pause row with none held: `NONE EQUIPPED` / `build one at a partner bench, then equip it` | `NONE YET` / `the Black Market dealer gives you one free` |
| companions popped in beside the owner (a bare SpawnActor) | every deploy materialises with the teleporter's arrival |
| the R.A.P.S. blast, the item-installed flash and the counter's LEGENDARY / cursed blast used `electric/fx_elec_burst_lg_z270_os` — a `gfx_debug_missing_fx` STUB that drew NOTHING | Der Eisendrache's teleport flash (`dlc1/castle/fx_elec_teleport_flash_lg`, the teleporter's own "bright discharge") |
| `partner part` prompt noun + icon (`i_tod_prompt_icon_partner_part`) | retired whole (noun, ICONS row, zone line, GDT block; the PNG moved to `archive/retired_20261004_partner_parts/`) |

Kept: the crown TEST benches (`TOD_PARTNER_TEST_BENCHES`, the tester kit: free equip / swap / dismiss; a dismissed
tester sees the gift prompt again), the companions themselves (stats, AI, items, freeze, rebuild), the spin.

The eight part MODELS (`tod_partner_*_part1/2`) stay in `tod_partners.zpkg`: `tools/partner/install_assets.py` writes
them and its manifest + `verify_assets.py` pin all twelve models. Nothing spawns them. Retiring them = the installer's
`split_parts`, the manifest, `verify_assets.py` (12 -> 4) and the 8 zpkg lines, one pass.

## 3. Rules + knobs

- **THE USER'S RULE: the gift never touches the luck bar.** `gift()` reads it for the LUCK box and never spends it; no
  points, no coin, no hot-streak result, no spin count. `test_spin.js` executes the whole gift and checks the body for
  every spending call (a negative control proves the spin still spends).
- **The companion is his the moment the reel shows it** (`level.tod_partner_gift_fn` -> `_tod_partners::gift_companion`
  right after `tod_spin_land`), and it deploys only when his screen closes (`freeze_reason` "owner_spin").
- **A gift tile is never anything else:** tile = 44 + companion + 1 (45..48); items are <= 39, CURSED is 60, a packed
  tease < 64. LOCKSTEP `_tod_shop.gsc` TOD_GIFT_TILE_BASE / TOD_SPIN_CODE_GIFT (8) / TOD_GIFT_SLOTS_MODE (4) /
  TOD_GIFT_POOL_MODE (5) / TOD_GIFT_COMPANIONS (4) with `TodSpinReel.lua` P3.GIFT, and `tools/ui_mockup/render_spin.py`.
- **Glyph pools are hard character limits:** the prize name pool is 16 (CIVIL PROTECTOR), the odds caption 32
  (the gift caption); the harness checks every gift line against its row's pool.
- **Never a size-1 PIL rank filter** (`MaxFilter(1)`): on this machine it is a hard "int divide by zero" crash (exit 127,
  no traceback).
- Knobs (all in `_tod_shop.gsc`): `TOD_GIFT_STEP_MAX_MS` 450 (the reel's last tile), `TOD_GIFT_OPEN_SECS` 0.5,
  `TOD_GIFT_READ_SECS` 3.2, `TOD_GIFT_VO_LAND_AT` 0.35 / `TOD_GIFT_VO_LAND_WAIT` 2.5 (the landing line), 
  `TOD_GIFT_VO_OFFER_CD` 20, `TOD_GIFT_NUDGE_SECS` 8.

## 4. Generated assets (never hand-edit)

- `tools/partner_shop/make_gift_art.py` -> `i_tod_spin_tile_gift` (the RARE tile in the companion's cyan, COMPANION at
  its foot from the map's glyph sheets), `i_tod_spin_banner_gift` (the LEGENDARY banner in cyan, ON THE HOUSE), and
  `i_tod_spin_ico_comp_<protector|talon|raps|cerberus>` (each docs/195 portrait cut square for the tile's window).
  `--check` is a build gate (bytes + GDT + zone + Lua); `--review` writes `art/dealer_gift/review/gift_art.png`.
- The six voice lines: `tools/black_market_vo/lines.json` (groups `gift_offer`, `gift_spin`, `gift_land`), generated with
  the shipping voice (generate.py), picked by measurement (voiced share 0.72-0.83, the shipped lines' range) in
  `picks.json`, shipped under the mask by `pick.py`.

## 5. Gates

- `tools/partner_shop/test_spin.js` (737): the dispatcher, the prompt (no lock word, no price, TO TAKE, fits the card's
  40-cell rows), the pick (executed: solo / co-op variety / all taken / his own never counts), the reel timing
  (executed), THE WHOLE GIFT executed against stubbed engine calls (the event order, his luck in the box, the hand-off
  at the landing, the empty slots, the unlock after the panel, the five refusals), the landing line's lane wait, the
  pool, the nudge, no stub effects (with the old stub as the control), LOCKSTEP with the reel and the renderer.
- `tools/partner/test_partners.js` (152): `gift_companion` executed (every companion, co-op ownership, refusals, a live
  tester's pick retired first with its health kept), the parts / workshop prompts retired whole, the tables kept, the
  arrival on every deploy, no stub effects.
- `tools/test_spin_reel.lua` (both lanes, art and flat): the gift reel (companion tiles only, his tile under the needle,
  no pour, no odds, the caption, the empty window, the pool), the landing (banner, grin, the portrait punch once, the
  name / role / status), SPIN TO FILL, box 4 back to SCRAP after a gift, an item spin after a gift untouched, every gift
  line inside its glyph pool, the companion row's new copy. 9 mutants on the Lua and 16 on the GSC, all caught.
- `make_gift_art.py --check`, `pick.py --check` (101 lines), `lint_tod_hints` (83 distinct strings, was 95),
  `lint_tod_assets`, arity, native API, the strict GSC lint, `test_dealer_house.js`, `test_shop.js`.

## 6. Logs (`[TOD_SHOP]`, `[TOD_PARTNER]`; both print in a normal match during bring-up)

`GIFT_BEGIN player= companion= luck_kept= seed= party=`, `GIFT_STEP` (every 10th), `GIFT_LAND ... given= luck_now=`
(luck_now must equal luck_kept), `GIFT_END`, `GIFT_REFUSED reason=down|menu|flying|has_companion|no_partner_module`,
`GIFT_VO_LAND dropped=1` (should be rare), `GIFT_NUDGE players=`; `[TOD_PARTNER] GIFT owner= type= name= hp= previous=
gifts=`, `INIT rev=2 ... source=dealer_gift`, `TABLE id=` x4 + `WORKSHOP ready`, and the usual `SPAWN` (the arrival
effect logs only a FAILURE, through `_tod_teleport`'s own dev logger: `asset_missing` / `host_failed`).

## 7. Open (the user's call)

- The workshop wings (1000 points each, at the run's end) now hold only their crafting tables. They could become
  something else (the bottom-of-tower bench room, a second Black Market) — not decided here.
- Should a co-op player be able to trade / re-roll his gift? Not built (one gift each; a tester can dismiss at a crown
  test bench and take another).

## Build

- LANDED 2026-10-04 12:52:35 in one step (37 files, 3-way merged against -a4's haven v5 + -5e's Map One migration;
  one hunk hand-resolved in `_tod_main.gsc` to keep -5e's `tod_base_sign::init()`).
- Every build gate on the repo after the landing: 125 / 0 failures (`tmp/dealer_gift/gates_repo.log`).
- FULL BUILD OK 13:34:58 (`tmp/dealer_gift/full2.log`; build 1 was refused at gdtdb because BlackOps3 started, nothing
  native ran): .ff 13:33:10, FF 233,681,472 B, geom_key REUSED the 12:43 bake, the 8 known-waived linker lines only.
- VERIFIED: the ledger carries the six gift images (fresh .iwi), `_tod_shop` / `_tod_partners` / `_tod_shop_vo` /
  `_tod_main`, the six Lua rawfiles and `dlc1/castle/fx_elec_teleport_flash_lg`, and no partner-part icon; all six
  `tod_spin_vo_gift_*` stems are in the fresh loaded bank and no `no_companion` line; deployed = repo, nothing synced
  after the .ff. The two retired wavs and the retired icon PNG remain, unreferenced, at the private tools root (the
  sync never deletes).
- UNPLAYED: the gift's pacing, the voice lines' fit, the pool / landing look and the arrival are the user's to judge.
