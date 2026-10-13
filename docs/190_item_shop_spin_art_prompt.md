<!-- art-pack
name: item_shop_spin
refs:
  docs/184_synthwave_ref/style_board.png | THE STYLE. The game's UI look: black glass plates, neon tube edges, magenta frame light, cyan focus. Match this above everything else. Attach to EVERY prompt.
  docs/184_synthwave_ref/world_city_ingame.png | THE WORLD. The game view this screen sits on top of: black towers outlined in neon. The machine must feel like part of this city.
  docs/190_ref/screen_layout_1280x720.png | THE LAYOUT. The whole spin screen at the moment a spin lands, drawn with FLAT PLACEHOLDER colours. Every piece in this pack goes where this picture puts it. Copy positions and sizes only, never these flat colours. Attach to EVERY prompt.
  docs/190_ref/frame_slot_map_2160x872.png | THE MACHINE FRAME's slot map: every area of the 2160x872 frame in exact pixels (legend under the picture). Attach to Prompt A.
  docs/190_ref/tile_slot_map_560x416.png | THE REEL TILE's slot map: the icon well, the name band and the rarity-word band on a 560x416 tile, in exact pixels. Attach to Prompt B.
  docs/190_ref/socket_slot_map_800x288.png | THE SLOT SOCKET's slot map: the icon well and the three text lines on an 800x288 socket, in exact pixels. Attach to Prompt F.
  i_tod_pm_ico_damage.png | A delivered WHITE glyph from the same game: the icon style for all nine item icons (flat, bold, pure white, soft glow, transparent background). Attach to Prompt C.
preview: 1280x720
-->

# 190 — THE BLACK MARKET SPIN: the Item Shop spin screen art (art request for docs/188)

STATUS: INSTALLED 2026-09-29 01:23 from `files - 2026-09-29T011305.667.zip` (all 26, exact
names/sizes, RGBA; archived at art/item_shop_spin/drop_2026-09-29/). Checks: the reel window
is alpha 0, the icons/flare/rays/socket/chip are pure white or neutral, every game-written
area is flat and dark, the baked words proofread (SCRAP reads "5CRAP" only because the map
face draws S like 5). Layout proof rendered from the installed files at the Lua's positions:
`docs/190_ref/installed_screen_1280x720.png` (`tools/partner_shop/render_spin_screen.py`).
Originally requested the same day (user: "Looks pretty bland without UI which i think we need
an asset request to wire some up"). Zip: `~/Downloads/tod_item_shop_spin_art_pack.zip`.

The first playtest (run `tmp/elite_tracking/runs/20260928_235530_153_19ead985`) proved the
mechanics end to end: 7 spins, Common and Epic prizes, one full-slot choice, zero UI
errors, `[TOD_PARTNER] ITEMS` applied every time. What it lacks is the look: the reel is
flat LUI quads and text. This pack replaces every quad with art.

## Repo side (not in the pack): the install

1. `.\tools\make_art_pack.ps1 -Inspect 'files (N).zip'`, LOOK at all 26, proofread the
   seven baked words (BLACK MARKET, COMMON, RARE, EPIC, LEGENDARY, SCRAP, BACK TO LUCK)
   against the glyph set, check every size and that the reel window of the frame is
   truly transparent (alpha 0 in x 80..2080, y 96..320).
2. Copy into `source_data/tod_ui_images/_images/`. All 26 are NEW names: one GDT block
   each (clone a `compressed high color` UI image block; every size here is a multiple
   of 4 ON PURPOSE, see memory `compressed-image-multiple-of-4`) + one zone `image,` line
   each. Tinted pieces (icons, socket, chip, flare, rays) are white by design: the code
   tints them with `setRGB`.
3. `TodSpinReel.lua`: every layout number comes from `tools/partner_shop/gen_spin_art_refs.py`
   (the same numbers that drew the slot maps; LOCKSTEP). Draw order inside the panel:
   frame (`i_tod_spin_frame`, over the strip, under the prize/slot rows) -> glass over the
   window -> needle. Tiles become `i_tod_spin_tile_<rarity>` + the item icon tinted by
   rarity (the Plate/Stripe/Foot quads and the tile's rarity text go). The prize banner
   becomes `i_tod_spin_banner_<rarity>`; the flare becomes `i_tod_spin_flare`, plus
   `i_tod_spin_rays` on Epic/Legendary. Slots become `i_tod_spin_socket` (tinted by
   rarity, grey when empty) + icon, focus = `i_tod_spin_socket_focus`, the fourth box =
   `i_tod_spin_scrap` (its baked words replace the SCRAP/BACK TO LUCK text). Chips become
   28x28 `i_tod_spin_chip` + the icon at 20x20. Title text goes (baked); LUCK text moves
   into the luck window.
4. `tools/test_spin_reel.lua` + `test_spin.js` updated for the image lane; lint_tod_assets
   GATE A must see all 26 zone lines. FULL build (GDT). Proof = fresh content-hash `.iwi`.

<!-- PACK:BEGIN -->
# The Black Market Spin: the Item Shop's spin screen

## What this is (read this first)

This is a zombies game. Every player has a small robot companion (a drone, a tank, a
rolling ball robot or a humanoid robot) that fights beside them. At a glowing street
kiosk run by a masked black-market dealer, the player can pay for a **spin**: a slot-machine
reel of item tiles rushes past a needle, slows down, and lands on ONE item for their robot
companion, in one of four rarities. Think of a loot-case opening in a shooter: the whole
point is the anticipation while the reel slows, and the burst when it lands.

The screen, top to bottom (see `reference/screen_layout_1280x720.png`):
1. a **machine frame** with the title **BLACK MARKET** and a small window where the game writes the player's luck,
2. the **reel window**: a strip of item tiles scrolls sideways behind glass, under a **needle** at the centre,
3. the **prize**: a big **rarity banner** (COMMON / RARE / EPIC / LEGENDARY) stamps down, with a **flash** behind it; the game writes the item's name and effect under it,
4. the companion's **three item slots** plus a **SCRAP** choice,
5. and, after the spin, three tiny **chips** in the corner of the normal game screen showing what the companion carries.

The game draws all the text that changes (item names, the luck number, effects, slot
labels). You draw the chrome, the tiles, the icons, the banners and the flashes.

## THE STYLE

**Match `reference/style_board.png` above everything.** Neon synthwave: dark violet-black
glass plates, thin violet-steel frames with NEON TUBE edges (a glass tube with a white-hot
core and a soft glow, never a flat painted stroke), hot magenta `#FF2BD1` frame light,
electric cyan `#1FE5FF` for rules, focus and "ready", deep violet `#7A46FF` for secondary
frames. Plates: `#0C0716` plate, `#140C24` panel, `#1F1336` header band, steel `#4A3A70`.
`reference/world_city_ingame.png` is the game world under this screen: black towers
outlined in neon. The machine must look like it belongs in that city.

**THE ONE EXCEPTION: the four RARITY colours.** They are a game signal and appear ONLY on
the rarity pieces (the tiles, the banners). Never use them for the frame:

| Rarity | Colour | Feel |
|---|---|---|
| COMMON | white-silver `#E9EEF5` | clean, plain, cool |
| RARE | electric blue `#3AA8FF` | a step up: a brighter tube, a soft inner glow |
| EPIC | purple `#B55CFF` | special: a double tube, corner accents, a charged look |
| LEGENDARY | gold `#FFC23D` | the jackpot: the richest piece in the set, sparks, filigree corners, radiant |

Each rarity must be unmistakable at a glance, even at small size and in motion. The
escalation from COMMON to LEGENDARY must be obvious: more light, more detail, more energy.

**NO RED ANYWHERE.**

## DELIVERABLES: 26 PNG files, exact names and sizes

Every file: PNG, RGBA (with alpha), EXACTLY the size listed (every size is a multiple of 4
on purpose; do not change any). Transparent means alpha 0.

| # | File | Size | What |
|---|---|---|---|
| 1 | `i_tod_spin_frame.png` | 2160 x 872 | the machine frame (Prompt A) |
| 2 | `i_tod_spin_glass.png` | 2000 x 224 | the glass over the reel window (Prompt A) |
| 3 | `i_tod_spin_needle.png` | 96 x 560 | the needle (Prompt A) |
| 4 | `i_tod_spin_tile_common.png` | 560 x 416 | reel tile, COMMON (Prompt B) |
| 5 | `i_tod_spin_tile_rare.png` | 560 x 416 | reel tile, RARE (Prompt B) |
| 6 | `i_tod_spin_tile_epic.png` | 560 x 416 | reel tile, EPIC (Prompt B) |
| 7 | `i_tod_spin_tile_legendary.png` | 560 x 416 | reel tile, LEGENDARY (Prompt B) |
| 8 | `i_tod_spin_ico_plating.png` | 208 x 208 | item icon, white (Prompt C) |
| 9 | `i_tod_spin_ico_overclock.png` | 208 x 208 | item icon, white (Prompt C) |
| 10 | `i_tod_spin_ico_hollow.png` | 208 x 208 | item icon, white (Prompt C) |
| 11 | `i_tod_spin_ico_sight.png` | 208 x 208 | item icon, white (Prompt C) |
| 12 | `i_tod_spin_ico_nano.png` | 208 x 208 | item icon, white (Prompt C) |
| 13 | `i_tod_spin_ico_arc.png` | 208 x 208 | item icon, white (Prompt C) |
| 14 | `i_tod_spin_ico_salvage.png` | 208 x 208 | item icon, white (Prompt C) |
| 15 | `i_tod_spin_ico_reboot.png` | 208 x 208 | item icon, white (Prompt C) |
| 16 | `i_tod_spin_ico_lucky.png` | 208 x 208 | item icon, white (Prompt C) |
| 17 | `i_tod_spin_banner_common.png` | 1600 x 208 | rarity banner (Prompt D) |
| 18 | `i_tod_spin_banner_rare.png` | 1600 x 208 | rarity banner (Prompt D) |
| 19 | `i_tod_spin_banner_epic.png` | 1600 x 208 | rarity banner (Prompt D) |
| 20 | `i_tod_spin_banner_legendary.png` | 1600 x 208 | rarity banner (Prompt D) |
| 21 | `i_tod_spin_flare.png` | 512 x 512 | white flash, tinted by the game (Prompt E) |
| 22 | `i_tod_spin_rays.png` | 1024 x 1024 | white light rays, tinted by the game (Prompt E) |
| 23 | `i_tod_spin_socket.png` | 800 x 288 | an item slot, white rim (Prompt F) |
| 24 | `i_tod_spin_socket_focus.png` | 832 x 320 | the "selected slot" ring (Prompt F) |
| 25 | `i_tod_spin_scrap.png` | 800 x 288 | the SCRAP choice (Prompt F) |
| 26 | `i_tod_spin_chip.png` | 112 x 112 | the tiny loadout chip, white rim (Prompt F) |

## THE PIECES, IN DETAIL

### A. The machine: frame, glass, needle

**1. `i_tod_spin_frame.png` (2160 x 872).** Shown at half size (1080 x 436) in the middle of
the screen. Follow `reference/frame_slot_map_2160x872.png` to the pixel:
- **Header band** x 0..2160, y 0..80: the `#1F1336` band with a thin cyan rule under it.
  Bake the title **BLACK MARKET** centred in **x 600..1560, y 8..72**, in our typeface, in
  magenta neon (like a lit sign), cap height about 44 px.
- **Luck window** x 1720..2120, y 12..68: an EMPTY dark window (plate colour) with a thin
  violet rim. The game writes "LUCK 80" inside. Nothing baked there.
- **Reel window** x 80..2080, y 96..320: **FULLY TRANSPARENT** (alpha 0), every pixel. The
  tiles scroll through here. Draw its neon rim OUTSIDE this box (in the 8-24 px around it):
  a cyan tube rim, like the glass front of a slot machine. The top centre of the rim, at
  about x 1040..1120, stays plain: the needle sits on top of it there.
- **Prize area** x 280..1880, y 348..604, **slot row** x 232..1928, y 640..784, and
  **controls line** x 280..1880, y 804..844: FLAT and DARK (plate `#0C0716` / panel
  `#140C24`). The game draws the banner, text and slots on top. No texture, no rules
  and no decoration inside these areas.
- **Everything else** is the machine body: dark violet-black glass with a magenta tube frame
  around the whole panel (see the style board's panel). You may add subtle machine
  details in the margins OUTSIDE the areas above: a few rivets, vents, thin cyan status
  lights, small corner bevels. Keep it dark and quiet: the reel is the star.
- The outer edge may have a soft magenta glow, fading to transparent at the image edge.

**2. `i_tod_spin_glass.png` (2000 x 224).** Laid exactly over the reel window, on top of
the scrolling tiles. It makes the tiles look like they are behind glass in a machine:
- the middle 60% is almost fully transparent, with only a faint diagonal glass sheen
  (a few very soft white streaks at 5-10% opacity);
- the left 400 px and the right 400 px fade from transparent to near-solid plate colour
  `#0C0716` at the very edge, so tiles fade in on one side and fade out on the other;
- faint horizontal scanlines across the whole piece at 4-6% opacity;
- NO frame, NO rim, NO text (the frame image draws the rim).

**3. `i_tod_spin_needle.png` (96 x 560).** It stands at the centre of the reel and marks the
winner. Mostly transparent:
- a **top arrowhead** in y 0..56 pointing DOWN (tip at y 56, centred at x 48),
- a **bottom arrowhead** in y 504..560 pointing UP (tip at y 504, centred at x 48),
- between them only a **hairline**: a 2-3 px glowing vertical line at x 47..49 at 50%
  opacity, so it never hides a tile's icon or words.
- Cyan neon tube with a white-hot core and a soft glow. Everything else transparent.

### B. The reel tiles (4 files, 560 x 416)

Each tile is one item on the reel, shown at 140 x 104 on screen, dozens rushing past per
second. The game draws the item icon and the item name on top. Follow
`reference/tile_slot_map_560x416.png`:
- **Icon well** x 176..384, y 32..240: an EMPTY dark window (a soft dark recess) where the
  game draws the item icon. Nothing baked inside it.
- **Name band** x 24..536, y 256..320: EMPTY and DARK. The game writes the item's name here.
- **Rarity word** x 40..520, y 336..400: BAKE the rarity word here, centred, in our
  typeface, in that rarity's neon colour: **COMMON**, **RARE**, **EPIC** or **LEGENDARY**.
- The tile itself: a black-chrome card with a neon tube rim in its rarity colour and a
  faint inner glow of the same colour. Keep a 12 px transparent margin on every side so
  the glow stays inside the image.
- Escalation: COMMON a single clean white-silver tube; RARE a brighter blue tube with a
  soft inner glow; EPIC a double purple tube with small corner accents and a charged
  shimmer; LEGENDARY a gold tube with ornate filigree corners, tiny sparkles and the
  strongest glow. All four share the same layout and the same empty windows.

### C. The nine item icons (208 x 208, pure WHITE)

These show what the item does. The game tints them in the rarity colour and shows them
at several sizes, from 52 px on the tiles down to **20 px** on the tiny chips, so each
must read at 20 px by silhouette alone. Style = `reference/i_tod_pm_ico_damage.png`:
flat, bold, **pure white** shapes with a soft white glow, transparent background, no
colour, no text, no numbers, no outline in another colour. Centre each shape and keep
about 16 px of empty margin.

| File | Item | Draw |
|---|---|---|
| `i_tod_spin_ico_plating.png` | PLATING (more health) | a heavy armour plate / shield with rivets |
| `i_tod_spin_ico_overclock.png` | OVERCLOCK (fires faster) | a microchip with a lightning bolt through it |
| `i_tod_spin_ico_hollow.png` | HOLLOW POINT (more damage) | a bullet whose tip is split open in a cross |
| `i_tod_spin_ico_sight.png` | LONG SIGHT (more range) | a sniper scope reticle with range ticks |
| `i_tod_spin_ico_nano.png` | NANO REPAIR (heals itself) | a wrench crossed with a plus sign, small hexagons around it |
| `i_tod_spin_ico_arc.png` | ARC CHAIN (shots jump between enemies) | a lightning bolt forking into three branches ending in dots |
| `i_tod_spin_ico_salvage.png` | SALVAGE (its kills pay more points) | a gear with a coin in its centre |
| `i_tod_spin_ico_reboot.png` | QUICK REBOOT (rebuilds faster) | a power symbol inside a fast circular arrow |
| `i_tod_spin_ico_lucky.png` | LUCKY CHARM (its kills give luck) | a four-leaf clover |

All nine must look like ONE family: same line weight, same glow, same visual size.

### D. The rarity banners (4 files, 1600 x 208)

The big stamp that lands when the reel stops, shown at 400 x 52 in the centre of the
screen. Each is a wide neon sign plate with its rarity word BAKED in big letters, centred,
in our typeface, in its rarity colour: **COMMON**, **RARE**, **EPIC**, **LEGENDARY**.
- Letters: a neon tube with a white-hot core, cap height about 120 px, generous spacing.
- Plate: dark glass, with a rim in the rarity colour.
- Escalation like the tiles: COMMON clean and simple; RARE with a blue glow bloom; EPIC with
  purple energy streaks off both ends; LEGENDARY gold, with sparks, small starbursts at both
  ends and the strongest bloom. The glow fades to transparent inside the image edges.

### E. The flash (2 files, pure WHITE, tinted by the game)

- **`i_tod_spin_flare.png` (512 x 512):** a soft round burst of light. A white-hot centre
  fading smoothly to fully transparent before the edges, with no hard ring. The game grows
  and fades it behind the landing tile and the banner.
- **`i_tod_spin_rays.png` (1024 x 1024):** 12 to 16 tapered light beams radiating from the
  exact centre, like god-rays. White, brightest at the centre, fading to transparent well
  before the edges, the gaps between beams transparent. It is used for EPIC and LEGENDARY
  only.

### F. Slots and chips

After the prize, the robot's three item slots appear with a SCRAP choice beside them.
Follow `reference/socket_slot_map_800x288.png` for the slot pieces.

- **`i_tod_spin_socket.png` (800 x 288):** one item slot, shown at 200 x 72. A dark glass
  plate with a **pure WHITE neon tube rim**: the game tints the whole image in the item's
  rarity colour (and grey when the slot is empty), so draw the rim white and the plate
  dark. An empty dark **icon well** at x 40..232, y 56..248 (the game draws the icon in it).
  The right side x 256..776, y 24..256 stays flat and dark: the game writes the slot label,
  item name and rarity there. Nothing baked.
- **`i_tod_spin_socket_focus.png` (832 x 320):** the ring that shows which slot is
  selected. It sits 16 px outside a socket on every side. A **cyan lit tube** rectangle
  following the socket's shape, with a soft cyan glow; everything inside it transparent.
- **`i_tod_spin_scrap.png` (800 x 288):** the fourth choice, "throw this prize away and
  get some luck back". Same plate shape as a socket but in its own colours: a violet rim,
  a cyan broken-glass / shatter glyph in the icon well (x 40..232, y 56..248), and BAKED
  text in our typeface: **SCRAP** big (cap height about 64 px, white neon) and **BACK TO
  LUCK** small beneath it (cap height about 28 px, cyan), both left-aligned in the text
  area x 256..776.
- **`i_tod_spin_chip.png` (112 x 112):** a tiny rounded-square chip shown at 28 x 28 in the
  corner of the normal game screen, three in a row. A dark plate with a **pure WHITE tube
  rim** (tinted by the game) and an empty centre where the game draws a 20 px icon. Keep
  the rim bold: it must read at 28 px.

## PASTE-READY PROMPTS

Attach `reference/style_board.png` and `reference/screen_layout_1280x720.png` to every
prompt, plus the extra files named in it. Our typeface is in `typography/`: every letter
you bake must use it.

**Prompt A: the machine.** Attach also `reference/frame_slot_map_2160x872.png`.
> Neon synthwave slot-machine frame for a video game UI, 2160x872 PNG with alpha. A dark
> violet-black glass machine body with a hot-magenta neon tube frame around the panel.
> Top header band (y 0-80) in #1F1336 with a thin cyan rule under it and the title BLACK
> MARKET as a magenta neon sign centred in x 600-1560, y 8-72, using the attached
> typeface. An empty dark luck window with a thin violet rim at x 1720-2120, y 12-68. A
> FULLY TRANSPARENT reel window at x 80-2080, y 96-320, framed from outside by a cyan
> neon tube like the glass front of a slot machine. Flat dark plate areas with nothing
> inside them at x 280-1880 y 348-604, x 232-1928 y 640-784 and x 280-1880 y 804-844.
> Subtle rivets, vents and small cyan status lights only in the margins. No red, no text
> other than BLACK MARKET. Follow the attached slot map to the pixel.
> Then: the glass overlay, 2000x224 PNG with alpha: transparent centre with a faint
> diagonal glass sheen, both 400 px ends fading to near-solid #0C0716, faint scanlines,
> no frame. Then: the needle, 96x560 PNG with alpha: a cyan neon arrowhead pointing down
> in y 0-56, one pointing up in y 504-560, joined only by a 2-3 px glowing hairline,
> everything else transparent.

**Prompt B: the tiles.** Attach also `reference/tile_slot_map_560x416.png`.
> Four slot-machine reel tiles for a neon synthwave game UI, each 560x416 PNG with alpha:
> COMMON (white-silver #E9EEF5), RARE (blue #3AA8FF), EPIC (purple #B55CFF), LEGENDARY
> (gold #FFC23D). Black-chrome card, neon tube rim and faint inner glow in the rarity
> colour, 12 px transparent margin. An empty dark icon well at x 176-384, y 32-240 and an
> empty dark name band at x 24-536, y 256-320. Bake the rarity word in the rarity colour
> centred in x 40-520, y 336-400 using the attached typeface. Escalating richness: common
> plain, rare glowing, epic double tube with corner accents, legendary gold filigree
> corners and sparkles. Same layout on all four. No red.

**Prompt C: the icons.** Attach also `reference/i_tod_pm_ico_damage.png`.
> Nine game UI icons, each 208x208 PNG with alpha, in the exact style of the attached
> white glyph: flat, bold, pure white, soft white glow, transparent background, no colour,
> no text. They must read at 20 px. 1 armour plate shield with rivets, 2 microchip with a
> lightning bolt, 3 bullet with a cross-split hollow tip, 4 sniper scope reticle with
> range ticks, 5 wrench crossed with a plus sign and small hexagons, 6 lightning bolt
> forking into three branches ending in dots, 7 gear with a coin in its centre, 8 power
> symbol inside a fast circular arrow, 9 four-leaf clover. One family: same weight, glow
> and size.

**Prompt D: the banners.**
> Four neon sign banners for a game loot reveal, each 1600x208 PNG with alpha. Dark glass
> plate, rim and letters in the rarity colour, the word centred in big neon-tube letters
> (cap height ~120 px) using the attached typeface: COMMON (white-silver #E9EEF5, clean),
> RARE (blue #3AA8FF, soft bloom), EPIC (purple #B55CFF, energy streaks off both ends),
> LEGENDARY (gold #FFC23D, sparks, starbursts at both ends, strongest bloom). Glow fades
> to transparent inside the image. No red.

**Prompt E: the flash.**
> Two white light effects for a game UI, PNG with alpha, pure white only: (1) 512x512
> soft round flash, white-hot centre fading smoothly to transparent before the edges, no
> ring; (2) 1024x1024 god-rays: 12-16 tapered beams from the exact centre, brightest at
> the centre, fading to transparent well before the edges, transparent gaps.

**Prompt F: slots and chips.** Attach also `reference/socket_slot_map_800x288.png`.
> Neon synthwave game UI pieces, PNG with alpha: (1) 800x288 item slot: dark glass plate,
> PURE WHITE neon tube rim (it gets tinted later), an empty dark icon well at x 40-232,
> y 56-248, the area x 256-776, y 24-256 flat and dark, no text. (2) 832x320 selection
> ring: a cyan lit neon tube rectangle following the slot's shape 16 px outside it, soft
> glow, transparent inside. (3) 800x288 SCRAP choice: same plate shape, violet rim, a cyan
> shatter glyph in the icon well, baked text in the attached typeface: SCRAP (big, white
> neon) and BACK TO LUCK (small, cyan) left-aligned in x 256-776. (4) 112x112 tiny chip:
> dark rounded-square plate with a bold PURE WHITE tube rim and an empty centre.

## HARD RULES

- Exact file names and exact sizes from the table. PNG, RGBA. Do not resize anything.
- Transparent (alpha 0) wherever this brief says transparent, above all the frame's reel
  window.
- White pieces are PURE white (icons, flare, rays, the socket rim, the chip rim): the game
  colours them. A tinted "white" breaks every rarity colour.
- The only baked words in the whole pack: BLACK MARKET, COMMON, RARE, EPIC, LEGENDARY,
  SCRAP, BACK TO LUCK. All in our typeface, all capitals.
- NO RED ANYWHERE. Gold only on LEGENDARY pieces.
- Areas the game writes into stay flat and dark: no texture, no rules, no decoration.

## DELIVERY CHECKLIST

- [ ] 26 files, names exactly as the table, sizes exactly as the table
- [ ] the frame's reel window (x 80..2080, y 96..320) is fully transparent
- [ ] BLACK MARKET, the four rarity words, SCRAP and BACK TO LUCK spelled right, in our typeface
- [ ] the four tiles and four banners read as four different rarities at a glance
- [ ] all nine icons pure white on transparent, one family, readable at 20 px
- [ ] flare, rays, socket rim and chip rim pure white
- [ ] no red anywhere

## DO NOT

- put any item name, number, luck value or slot label into any image (the game writes them)
- colour the icons, the flare, the rays, the socket rim or the chip rim
- draw anything inside the frame's reel window, or put texture in the areas the game writes into
- use the rarity colours on the frame, or gold outside the LEGENDARY pieces
- change any size, or add, rename or merge files
<!-- PACK:END -->
