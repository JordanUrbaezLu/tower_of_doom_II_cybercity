# 188 — THE BLACK MARKET SPIN (companion items)

GIFT 2026-10-04 (docs/209): a player with NO companion no longer meets a locked "companion required" card. His
first use is THE DEALER'S GIFT - a free 30-tile COMPANION reel on this spin's machinery, luck and points
untouched, the companion handed over at the landing and its three empty slots shown (SPIN TO FILL). The paid
spin below is unchanged and is what every later visit buys.

ONE NAME since 2026-09-29 (user: *"The Item Shop / Black Market is confusing. Lets just rename it Black Market all
together and update the model with Blender MCP"*): the shop is the **BLACK MARKET** everywhere a player looks: the
prompt ("BLACK MARKET - Spin for a companion item ..."), the prompt noun, the neon sign on the model (rebuilt in
Blender MCP, `tools/partner_shop/18_black_market_sign.py`, docs/161) and the spin screen. "Item Shop" survives only
in the user quotes and the history below. Internal names (`_tod_shop.gsc`, `tod_shop_*` models, `art/partner_shop/`)
are unchanged.

OWNER since 2026-09-29: session d2 (the user assigned it the Black Market screen, animations and everything; 9c keeps the
item EFFECTS in _tod_partners.gsc - ping 9c before changing an item's value or adding / removing an item).
STATUS 2026-09-29: IMPLEMENTED, BUILT (23:18 gsc3; in d2's 23:32 build) and PLAYED once (run 20260928_235530):
7 spins, Common + Epic prizes, one full-slot choice, zero UI errors, items applied. User: "bland without UI" -> art requested (docs/190).
Files: `_tod_shop.gsc` (the spin), `_tod_partners.gsc` (item effects + chips),
NEW `ui/uieditor/widgets/HUD/AetheriumWidgets/TodSpinReel.lua` (zoned in the
.zone; built by `tod_upgrade.lua`), `ZMCursorHintNew.lua` (noun "black market"; "item shop" until 2026-09-29).
Gates: `tools/partner_shop/test_spin.js` (210), `tools/test_spin_reel.lua`,
`tools/partner/test_partners.js` (108), `lint_tod_hints` route row.

User (2026-09-28): *"Players love the gamble system ... a rotating carousel or
spinning wheel. For the item shop they will have items for the AI Companion you
hold. All items will be generic enough where they apply to all companions. The
wheel will spin and select an item and rarity. Your luck will be used on spin
... Trigger will be an active Item Shop. We can make the crown item shop active
in dev mode ... think of the experience first."* Then: *"AI Companions can have
3 items equipped at once, none can be the same and each item has a rarity"*
and *"During use of the item shop you cannot be targeted by enemies."*

## 1. The experience (what the player feels, in order)

1. **The pitch.** The lit Black Market's prompt: `BLACK MARKET - Spin for a companion
   item / Your luck sets the odds $2500`. Without a companion it says so, and it
   costs nothing to walk away.
2. **The buy.** Hold USE. You are locked in and **untargetable** (zombies drop
   you as a target, and nothing can hurt you until the spin is over). The shop
   **crackles**: its sparks go off at the counter.
3. **Your luck goes in.** The strip slams onto the screen with `LUCK 80` on it.
   Your luck bar **drains to zero**: it is paid into the machine. **Luck is
   visible on the strip.** The filler tiles are drawn with the same odds your
   luck bought, so a full bar puts noticeably more blue, purple and gold on the
   reel. You can see what your luck did before the reel even moves.
4. **The spin.** Tiles rush past a centre needle. Every tile that passes ticks.
   The reel slows on a cubic curve. The last five tiles each land with a rising
   luck-pip note, so the ear counts down with the eye.
5. **The tease.** When the prize is not Legendary, the tile just past the
   needle is often one rarity better: "so close". When the prize IS Legendary,
   the reel all but stops on the tile before it. That is the heartbeat, and then
   it rolls over. (REPLACED 2026-10-02 by docs/201: the silent 45% tease is now
   STOPPED SHORT / SLIPPED PAST on 30% of non-Legendary spins, with motion, sound
   and the dealer, and THE HOT STREAK heats the EPIC/LEGENDARY odds. See docs/201
   section 10.)
6. **The hit.** The winning tile flares in its rarity colour, the banner stamps
   `EPIC`, and the item's name and exact effect at that rarity appear. The sound
   scales with the rarity. Epic and Legendary also throw sparks off the shop, and
   Legendary adds a blast and a thunder clap. On Epic or Legendary your
   **teammates are told** (`NAME PULLED A LEGENDARY OVERCLOCK`).
7. **Socket it.** The companion's three slots appear under the prize.
   - **Empty slot:** it sockets itself.
   - **You already hold that item at a lower rarity:** it upgrades in place.
     The prize never duplicates a slot.
   - **All three slots full with other items:** you choose. Use TACTICAL and
     LETHAL to move between SLOT 1 / SLOT 2 / SLOT 3 / SCRAP, and hold JUMP or
     USE to confirm (the card panel's grammar). SCRAP turns the prize back into
     luck. Timing out keeps your slots and scraps the prize, so nothing you own
     is ever lost to a timer.
8. **Payoff.** Your companion flashes as the item installs. The loadout shows
   as three rarity-coloured chips on the companion's status plate for the rest
   of the match.

### Design calls made here (the user may overrule any of them)

- **Luck is SPENT by a spin**, the way a card deal spends it. That makes the
  shop and the card deals compete for the same bar: spin now, or bank it for the
  next deal.
- **No dead spins.** The prize is never an item you already hold at the same or
  a higher rarity. Rarity is rolled first, then the item is drawn from what
  would actually be new or an upgrade. Every spin changes your companion unless
  you scrap it yourself.
- **Loadouts are PER COMPANION** ("AI Companions can have 3 items"). Each of
  the four companions keeps its own three slots, and a spin goes to the one you
  hold. Swapping companions swaps loadouts. You must have a companion equipped
  to spin; a destroyed one that is rebuilding still counts.
- **Flat price, 2500** (`TOD_SPIN_COST`). One constant keeps the prompt to one
  permanent hint string.
- **The world keeps running.** The spinner is untargetable and cannot be hurt,
  so no world pause is needed, and co-op teammates keep fighting.
- **The rarity ladder is docs/187's**: COMMON / RARE / EPIC / LEGENDARY in
  white / blue / purple / gold, with the same empty-to-full odds and the same
  full-bar Epic and half-bar Rare guarantees. The cards and the shop teach the
  player one ladder.

### Pass 2 (2026-09-29, after the first playtest; user: "Double check for bad player experiences or UI issues. Also the HUD should not show while this is happening")

- **The HUD hides for the whole spin.** The reel owns the `"spin"` key of the
  shared HUD veil (`TodHudVeil.lua`, built with the card reveal): every Aetherium
  widget, the cursor hint, the gauge, the luck bar and the damage numbers hide,
  and so do the companion status plate (a LUI widget in the veiled layer since PK08,
  2026-10-05) and the elite health bars (server hudelems, hidden per player on
  `tod_menu_frozen || tod_solo_upg_active`, which also covers card deals). A 40 s watchdog and the reel's close hook release the veil, so a lost
  event can never leave the HUD hidden. The small center messages stay.
- **The right prompt, or none.** A player with a companion sees the buy prompt, a
  player without one sees a locked "companion required / Build one at a partner
  bench" card, and the spinner sees no prompt at all (two constant hints, per-player
  trigger visibility).
- **No accidental losses in the slot choice** (the first playtest replaced HOLLOW
  POINT 0.65 s after the choice appeared): focus starts on the weakest slot only when
  the prize beats it, otherwise on SCRAP; for the first 0.6 s nothing confirms; a
  button already down must be released first. `test_spin.js` runs the real choice
  code with simulated input, including that exact case.
- **The result says what happened.** After a socket: "SOCKETED / UPGRADED IN SLOT N"
  with that slot ringed in its rarity colour; after a scrap: "SCRAPPED FOR N LUCK".
- **Fair hand-back.** 1.5 s of invulnerability after the panel closes (targetable
  again): zombies that idled beside an untargetable player cannot land a hit the
  instant control returns.
- **Card deals never collide with a spin.** Every wait in a spin gives way at once to
  a world pause (the reel hides, then reopens with the prize repainted); luck is paid
  at the purchase, before any wait; and the spin never unfreezes a player a deal is
  holding.
- **One sound language with the cards:** COMMON the card land, RARE/EPIC the sting,
  LEGENDARY the jackpot sound plus a heartbeat in the final crawl; only a LEGENDARY is
  announced to teammates (`PULLED A LEGENDARY <ITEM>`, the card alert sound). The reel
  ticks at most every 100 ms (a tick per server frame was a buzz).
- **UI fixes:** the reel's edge masks stuck 100 px out of both sides of the panel
  (drawn from the screen edge) - now inside the panel; placeholder colours follow the
  synthwave theme (magenta frame/title, cyan rules/needle/focus) until the docs/190 art
  lands; the loadout chips moved up off the companion bar's name label.
- **Companion fixes:** NANO REPAIR no longer heals during a world pause; QUICK REBOOT
  socketed mid-rebuild shortens the running rebuild too.

### Pass 3 (2026-09-29, session d2; user: "You will be responsible for the Item Shop Black Market screen and animations and everything")

Found by the new timed renderer (`tools/ui_mockup/render_spin.py`, the real TodSpinReel.lua on
_tod_shop.gsc's exact schedule): for the ~7 s the reel spins, the lower 60% of the panel was an
empty dark box, the world behind was not dimmed, the needle never moved, the luck counter just sat
there, and nothing reacted. Before/after: `docs/188_ref/pass3_before_after_midspin.png`.

- **The slam and the room.** The panel drops in from 26 px above and settles (Bounce, 200 ms) and
  the room behind it dims to 55% black; it drops out 22 px on the close.
- **The panel says what the spin is FOR.** The companion's three slots show from the open (the
  server sends `tod_spin_slots` mode 0 with `tod_spin_open`, and again on a resume), with
  `FOR YOUR <COMPANION>` under THE ODDS.
- **THE ODDS.** Four rarity segments show the TRUE odds the spin rolls with, guarantees included
  (`effOdds`, LOCKSTEP with `roll_rarity`: 50+ luck = no COMMON, 100 = EPIC / LEGENDARY only); the
  caption says `YOUR LUCK SETS THE ODDS` / `RARE OR BETTER GUARANTEED` / `FULL LUCK - EPIC OR BETTER`.
- **THE POUR (0.6 s).** The LUCK counter drains to 0 into the machine, luck motes fly from the LUCK
  box into the reel, and the odds slide from the empty-bar line to the bought odds. The server waits
  `TOD_SPIN_POUR_SECS` 0.95 (was 0.35) before the first step (LOCKSTEP `P3.POUR_MS` + the slam).
- **The machine moves.** The needle kicks on every tile; light pulses run along the title rail and
  the reel window's lower rail one hop per tile, so they race and then crawl with the reel.
- **The stop.** The last step runs 26 px past the prize and settles back onto it (Bounce).
- **The hit** speaks the card reveal's language (its generated sprites via the `TodCardArt`
  manifest): a ring for RARE+, shards + the screen-edge glow for EPIC+, a gold flash and a shake for
  LEGENDARY, on top of the flare / banner stamp / rays. It plays ONCE per spin (the server re-sends
  `tod_spin_land` when a slot choice starts; the second stamp read as a stutter).
- **The socket.** The prize's icon flies from the reel into its slot (320 ms), the slot's icon
  appears on arrival and the slot flashes; a repaint after a pause never flies twice.
- **The scrap.** The prize breaks into shards at SCRAP and its luck flies back: the counter counts
  up to the refund.
- **The chips.** The chip of the item just socketed pulses twice when the HUD comes back.
- Gates: `tools/test_spin_reel.lua` (pass 3 block with the FX sprites loaded, both lanes; odds bar
  = the roll at 7 luck values; 4 negative controls), `tools/partner_shop/test_spin.js` 265 (pour
  lockstep, companion names = `_tod_partners` define order, guarantees, slots from the open).
- BUILT in session 61's combined FULL BUILD OK 11:49:36 (tmp/transit_bay/full1.log), FF 221,747,008 B, verified (ledger, deployed = repo, nothing synced after). UNPLAYED.
- ~~Still owed~~ LANDED the same day (below): the docs/195 art and the docs/194 sound kit.

**Pass 3 art + sound (2026-09-29 12:28, d2; docs/195 drop + 9c's docs/194 install):**
- **THE DEALER** (left portrait window, 144 x 144 frame at (144, 284), LOCKSTEP docs/195): idle at
  the open; he leans in to WATCH on the last four slow tiles; at the hit he SHRUGS (COMMON), GRINS
  (RARE / EPIC) or throws up his arms (JACKPOT, LEGENDARY). A new pose punches in (a little big,
  bouncing to size, 160 ms) with a flash in the prize's colour; once per spin (the re-sent land never
  repeats it). His plate says THE DEALER in his mask's red.
- **THE COMPANION** (right window at (992, 284)): the robot that gets the item, its name on the
  plate; the window is hidden when the loadout never arrived (never an empty frame). When the prize's
  icon lands in its slot the companion's window flashes the prize's colour (the power flowing in).
- **SPEED STREAKS** over the reel (inside the reel's clip, under the glass): 0.55 at 60 ms a tile,
  thinning to nothing by 320 ms, gone at the hit.
- **THE SOUNDS** (`_tod_shop.gsc`): coin at the buy, open at the slam, the luck pour (luck > 0), the
  lever on the first tile, three rotating reel ticks, five crawl notes climbing a semitone a tile, the
  stop clunk then the card-reveal sting, socket / upgrade clicks with the flying icon, the scrap, the
  power-down at the close. The dealer's voice: a buy line on 70 in 100 spins, "meh" on half the
  COMMONs, always on EPIC / LEGENDARY (after the sting), never on RARE, "come back soon" on 35 in 100.
- Gates: `test_spin_reel.lua` pass 3 art block (6 negative controls), `test_spin.js` 307 (every alias
  the spin can play exists; the borrowed sounds are gone). See: `render_spin.py`.
- BUILT: FULL BUILD OK 12:34:09 (tmp/card_v2_classes/full1.log; map compile + bake REUSED by geom_key), FF 224,798,528 B, all 45 card2 + 37 spin images and todspinreel / todcardart / todpull / tod_upgrade / _tod_shop in the ledger, streamed bank 354.4 MB, diffs clean, nothing synced after. UNPLAYED.

### The AI COMPANION row (2026-09-29, session d2; user: "there is an upgrade in the pause menu. That shows AI companion. I don't think it's wired up yet, to the actual companion that the player has. So we need to wire it all up. Make sure the upgrades are there as well")

The first row of the pause menu and of the scoreboard is the companion you hold, live:

| | pause menu | scoreboard |
|---|---|---|
| well | the companion's portrait (docs/195 art) | same, smaller |
| name | CIVIL PROTECTOR / TALON / R.A.P.S. / CERBERUS | name + " - " + short state; amber while destroyed |
| where the pips go | its three items as the HUD's loadout chips: rarity-tinted chip + item icon; an empty slot is a dim rim | same |
| blue line | the item names ("PLATING, ARC CHAIN") or NO ITEMS - SPIN AT THE BLACK MARKET | same |
| grey line | ACTIVE - HEALTH 85% (green), DESTROYED - BACK IN 23 sec (amber), ON ITS WAY | (no third line) |
| nothing held | dimmed: AI COMPANION / NONE EQUIPPED (- N BUILT) / build one at a partner bench, then equip it | same, no state |

The data, one lane each way:
- **Server** `_tod_partners.gsc push_state( s )`, from `manager()` after `push_hud`, sends
  `tod_ptn_state` ( companion + 1, state, value, built mask ) ONLY when that signature changes. State:
  0 none held, 1 active (value = health %, 5 steps, never 0 while alive), 2 destroyed (value = whole
  seconds to rebuild, rounded up), 3 held but not out (on its way, or the owner is down or dead).
  `push_items` clears the signature, so an equip, swap, dismiss, socket or respawn re-sends at once.
  Logs `[TOD_PARTNER] UI_STATE` on transitions only.
- **The HUD status plate** (PK08, 2026-10-05, replaces `status_hud`'s three stock-font hudelems):
  `push_hud( s )` sends the owner `tod_ptn_hud` ( companion + 1, state, value, rebuild length,
  flags 1 frozen with its owner / 2 owner dead ) on change and re-sends it every 3 s;
  `TodCompanionPlate.lua` (in tod_upgrade.lua's veiled HudOnly) draws the portrait, the name and
  state in the typeface and the bar; the three item chips sit on its top edge (canvas right 1190,
  bottom 520). Logs `[TOD_PARTNER] HUD` on transitions only.
- **HUD** TodSpinReel.lua (always open) records it as `CoD.TodCompanion` together with every
  companion's items (`tod_ptn_items`), and `CoD.TodCompanionDescribe()` says the whole row from the
  spin's own tables (`CoD.TodCompanionInfo`: names, portraits, item names / icons, rarity colours).
  The two menus only lay it out, so nothing can drift from the spin.
- The row is a snapshot when the menu opens (in solo the world is paused anyway).
- **The item line fits by rule**: past 35 characters the longest full names give way to their chip
  labels one at a time ("HOLLOW POINT, QUICK REBOOT, LUCKY CHARM" = 266.5 of the row's 261 units ->
  "HOLLOW, QUICK REBOOT, LUCKY CHARM"). Measured over every loadout in the map TTF: the worst is 241.
- Gates: `render_menus.py --check` renders a held companion per class (the worst cases on purpose),
  `test_spin.js` checks the lanes, `test_spin_reel.lua` drives the events through the describe
  (loadouts per companion, every state, all 504 three-item loadouts under 35 characters, garbage args).

## 2. The items (generic: every companion)

| # | Item | COMMON | RARE | EPIC | LEGENDARY |
|---|------|--------|------|------|-----------|
| 1 | PLATING | health x1.25 | x1.5 | x1.8 | x2.2 |
| 2 | OVERCLOCK | fire rate x1.15 | x1.3 | x1.5 | x1.8 |
| 3 | HOLLOW POINT | damage x1.2 | x1.4 | x1.7 | x2.1 |
| 4 | LONG SIGHT | range x1.2 | x1.35 | x1.55 | x1.8 |
| 5 | NANO REPAIR | heals 1% max HP/s | 2% | 3% | 5% |
| 6 | ARC CHAIN | shots arc to 1 more at 30% | 1 at 50% | 2 at 50% | 3 at 60% |
| 7 | SALVAGE | its kills pay +10 | +25 | +40 | +60 |
| 8 | QUICK REBOOT | rebuild 34 s (was 45) | 25 s | 17 s | 10 s |
| 9 | LUCKY CHARM | its kills give x1.25 luck | x1.5 | x2 | x2.5 |

All numbers live in `_tod_shop.gsc` (`item_value`) and are applied by
`_tod_partners.gsc` through `tod_shop::item_mult` / `item_rarity` / `item_value`.
Range also stretches R.A.P.S.'s hunt radius, its blast radius and every
companion's target search. ARC CHAIN on R.A.P.S. arcs from the blast to zombies
just outside it. Arcs reach 300 units (`TOD_PTN_ARC_R`). PLATING re-scales a
live companion's health the moment it is socketed. QUICK REBOOT also sets the
length of the HUD rebuild bar.

## 3. Odds (docs/187, per spin)

| Luck bar | Common | Rare | Epic | Legendary |
|----------|--------|------|------|-----------|
| Empty    | 56     | 27   | 13   | 4         |
| Full     | 36     | 36   | 20   | 8         |

A straight line between the two rows. A bar at 100 guarantees at least EPIC,
and 25% of those guaranteed spins are LEGENDARY. A bar at 50 or more guarantees
at least RARE. The filler tiles use the same line.
THE HOT STREAK (docs/201, 2026-10-02) multiplies the EPIC and LEGENDARY slices by
1.15 / 1.30 / 1.50 (WARM / HEATING UP / ON FIRE), taken from COMMON; THE ODDS bar,
its caption (`HOT STREAK - BETTER ODDS`) and the filler tiles show it. The
guarantees ignore heat.

## 4. Engine plan (zero new clientfields, zero new sound assets)

- `_tod_shop.gsc` owns the spin. It spawns ONE `trigger_radius_use` in front
  of the active shop's counter (local -Y is the front, 96 out) and moves it
  whenever `activate()` moves the active shop. The hint is ONE constant string,
  and "black market" is a TOD_NOUNS entry ("item shop" until 2026-09-29).
- **Server-driven reel.** `tod_spin_open(seed, prize, tease, luck*64+land)`
  opens it. The Lua builds the filler from the seed and luck with its own
  deterministic LCG, because the filler is cosmetic and the server never needs
  it. Then one `tod_spin_step(index, ms)` per reel step: the Lua tweens the strip
  one tile over `ms`, and the server plays the tick on the same step. They cannot
  drift, and a dropped event only skips a tween. `tod_spin_land`,
  `tod_spin_slots` (the three slots and the focus/mode) and `tod_spin_end`
  finish it.
- `tod_ptn_items(s1, s2, s3, companion+1)` feeds the three persistent chips.
  It is sent on every loadout or companion change and on spawn.
- **Untargetable:** stock's `zm_utility::increment_ignoreme` refcount, plus
  `EnableInvulnerability`. The invulnerability is re-asserted every tick of the
  session, so a world-pause release in the middle of a spin cannot strip it. On
  exit it is dropped only if no world pause holds it (`tod_pause_invuln`).
- **Frozen:** `tod_upgrades::menu_freeze` (movement pinned, weapons off, the
  raw button reads live), the card panel's own lane.
- Sounds are existing aliases: `tod_ui_tick` (each tile), `tod_luck_pip06..10`
  (the last five), `tod_card_land` / `tod_ui_lock` / `tod_super_sting` /
  `tod_ultimate_sting` (the landing by rarity), `tod_shop_spark_1..3` (3D, at
  the counter), `tod_thor_clap` (Legendary).
- Dev mode (`level.tod_dev`): the crown shop is ACTIVE from the first frame
  instead of waiting for power (user: "make the crown item shop active in dev
  mode").

## 5. Logs

`[TOD_SHOP] SPIN_*` (in `_tod_shop.gsc`): TRIGGER, REFUSED (reason), BUY
(cost, luck, odds), ROLL (rarity, item, pool, guarantee), STEP (every 10th),
LAND, SOCKET (slot, auto/choice/timeout), SCRAP (luck back), END (invuln and
ignoreme restored). `[TOD_PARTNER] ITEMS` logs each companion's applied
multipliers whenever the loadout changes.

## 6. Open (the user's call)

- ART: INSTALLED 2026-09-29 01:23 (docs/190 drop, 26 images, `USE_SPIN_ART` in TodSpinReel.lua;
  the flat-quad lane stays behind the flag). Was REQUESTED 2026-09-29 as docs/190 (26 files: machine frame, glass, needle,
  four rarity tiles, nine white item icons, four rarity banners, flare + rays, socket,
  focus ring, SCRAP, chip; zip `~/Downloads/tod_item_shop_spin_art_pack.zip`). Until it
  lands the reel is flat quads + text. Layout numbers: tools/partner_shop/gen_spin_art_refs.py.
- Price curve, and whether luck is spent or only read.
- Whether workshop shops outside the crown get the spin too. Today the only
  shops are the crown's.
