# 184d — SYNTHWAVE PROMPT CARDS: the prompt cards redrawn in the neon synthwave theme

<!-- art-pack
name: synthwave_prompt_cards
refs:
  docs/184_synthwave_ref/style_board.png | THE STYLE. The new neon synthwave look: palette, tube frames, focus / ready / locked / rampage states. Match this above everything else.
  docs/184_synthwave_ref/world_city_ingame.png | THE WORLD. The game view this UI sits on top of: black towers outlined in neon. The UI must feel like part of it.
  docs/183_prompt_ref/slot_map_924x304.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). THE SLOT MAP. Every box the game writes into, in exact pixels on the 924x304 card. Your frame, rules and icon well must sit on these lines. Read the legend under the card.
  docs/183_prompt_ref/current_card_in_use_BEING_REPLACED.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). The CURRENT card as the player sees it (old cyan look), with example text in place. Shows what goes where. Do NOT copy its style.
  i_tod_prompt_chassis.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). The CURRENT card frame, empty (old style). Same size and same slot positions as the new one you draw.
  i_tod_prompt_chassis_wide.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). The CURRENT wide card (old style), used for the longest perk. Shows how the wide card differs: only the text area is longer.
  docs/183_prompt_ref/current_icons_BEING_REPLACED.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). The CURRENT ten card icons (old cyan cartoon style). Every one is redrawn. Same objects, new style.
  docs/180_pause_menu_ref/target_reference.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). THE STYLE. The approved pause menu. The cards must look like the same product.
  docs/182_hud_ref/round_badge_as_installed_mock.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). THE STYLE, newest approved piece: the round badge and luck plate. Match this frame weight, plate colour and magenta edge light most closely.
  i_tod_pm_row.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). Delivered pause-menu row card: plate material and frame weight to match.
  i_tod_pm_btn_focus.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). Delivered focused button: the magenta glow to match.
  i_tod_pm_ico_damage.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). Delivered WHITE glyph: the icon style (flat, bold, white, soft glow) for every icon in this pack.
  i_tod_h2_round_badge.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). Delivered round badge: its empty dark window is the look for the icon well.
  i_tod_perk_jugg.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). A perk logo. KEPT as is: the perk card draws the perk's own logo in the icon well, so the well must look right around a colourful logo too.
preview: 1280x720
-->

> **STATUS: REQUESTED 2026-09-26** (user, after seeing the red prompt-card drop: "I kinda want
> a different theme tho" -> chose NEON SYNTHWAVE for the WHOLE UI). NOTHING INSTALLED.
> 17 files. Same names, sizes and slots as 183_prompt_cards_v2_art_prompt.md, so the install is a FILE SWAP plus the
> code tints listed in docs/184_synthwave_theme.md. The red set stays installed until the
> synthwave drop lands.

<!-- PACK:BEGIN -->
# Synthwave prompt cards: redraw the prompt cards in the new neon synthwave theme

## THE THEME: NEON SYNTHWAVE (this overrides every colour below)

This set was first drawn in a red "Fallen" style. **The game's look has changed to NEON
SYNTHWAVE.** Redraw every file in the list below in the new style. Keep every shape,
position, size, baked word and empty area exactly as the spec further down says. Change
the look only.

**Match `reference/style_board.png` above all.** `reference/world_city_ingame.png` is the
game world this UI sits on top of: black towers outlined in magenta, cyan, violet and
gold neon. The UI must feel like part of that city.

- **Plates:** dark violet-black glass. Plate `#0C0716`, panel `#140C24`, header band
  `#1F1336`. Flat and dark wherever the game draws text.
- **Frames:** thin violet-steel lines (`#4A3A70`) with a NEON TUBE edge: a glass tube with
  a white-hot core and a soft glow, not a painted stroke.
- **Neon colours:** hot magenta `#FF2BD1` for frame light, electric cyan `#1FE5FF` for
  rules, focus and "ready", deep violet `#7A46FF` for secondary frames and the
  "dark card" (`_violet`) twins. Sunset orange `#FF8A3D` only as the RAMPAGE inner line.
  Gold `#F5D742` only for the points glyph.
- **NO RED ANYWHERE.** Wherever the spec below says red, read it like this:

| The spec says | Draw it as |
|---|---|
| red / blood-red / crimson edge light, red frame glow | a hot MAGENTA neon tube |
| a red rule, underline, slash, double slash or divider | a thin CYAN neon line |
| a word baked in red (for example **UPGRADES**) | the same word in MAGENTA neon |
| the red "focused" glow | a CYAN lit tube |
| the red "ready" or "active" glow on a tile | a MAGENTA lit tube |
| a lit red dot or pip | a lit CYAN pip |
| a dim, dark-red or "locked" state | a DEAD tube: unlit, grey-violet, no glow |
| a RAMPAGE twin | hot MAGENTA frame + a SUNSET ORANGE inner line, faint embers |
| a "violet" twin | a deep VIOLET `#7A46FF` tube (keep it violet) |
| grey text | pale lavender-grey `#B8AED8` |

- **Backdrops only** (full-screen `_backdrop` files) may carry a faint magenta horizon
  grid and a purple haze at the edges, still transparent in the middle. No grid anywhere
  else, and never behind text.
- The baked words and the typeface rules are unchanged: use the letters in `typography/`.

## Files to deliver (17, exact names and sizes, every size a multiple of 4)

| File | Size (px) |
|---|---|
| `i_tod_prompt_chassis.png` | 924 x 304 |
| `i_tod_prompt_chassis_wide.png` | 1200 x 304 |
| `i_tod_prompt_icon_altar.png` | 256 x 256 |
| `i_tod_prompt_icon_crate.png` | 256 x 256 |
| `i_tod_prompt_icon_crown.png` | 256 x 256 |
| `i_tod_prompt_icon_door.png` | 256 x 256 |
| `i_tod_prompt_icon_extract.png` | 256 x 256 |
| `i_tod_prompt_icon_pap.png` | 256 x 256 |
| `i_tod_prompt_icon_perk.png` | 256 x 256 |
| `i_tod_prompt_icon_power.png` | 256 x 256 |
| `i_tod_prompt_icon_rampage.png` | 256 x 256 |
| `i_tod_prompt_icon_teleporter.png` | 256 x 256 |
| `i_tod_prompt_chassis_locked.png` | 924 x 304 |
| `i_tod_prompt_icon_partner_bench.png` | 256 x 256 |
| `i_tod_prompt_icon_partner_part.png` | 256 x 256 |
| `i_tod_prompt_icon_alarm.png` | 256 x 256 |
| `i_tod_prompt_icon_generic.png` | 256 x 256 |

**Do NOT redraw:** nothing: every file in this pack is redrawn.

Read the ORIGINAL SPEC below for what each file is, its baked words and its empty areas.
It is correct in every respect except colour: follow it, but colour everything with the
theme above. Where the spec's file list and the list above disagree, the list above wins.

## ORIGINAL SPEC (colours already re-worded for synthwave; if any colour word below still disagrees with the theme above, the theme wins): Prompt cards: new art for every "press a button here" card in the game

### What this is

When a player walks up to a door, a perk machine, the Pack-a-Punch or any other object,
a small card pops up on screen: an icon on the left, a title, one or two lines of text,
and a footer that says which button to hold, with a price on the right. You are
redrawing that card and its icons in the game's new neon synthwave style, the same look
as the approved pause menu (`reference/target_reference.png`) and the newest round
badge (`reference/round_badge_as_installed_mock.png`).

**The game draws all the text itself.** You draw only the empty card frame and the
icons. Leave every text area empty.

### Deliverables (17 files, all PNG with transparency)

| File | Size (px) | What it is |
|---|---|---|
| `i_tod_prompt_chassis.png` | 924 x 304 | The card frame, EMPTY. Normal state. |
| `i_tod_prompt_chassis_wide.png` | 1200 x 304 | The same frame with a longer text area (276 px longer). |
| `i_tod_prompt_chassis_locked.png` | 924 x 304 | The "you can't do this yet" twin of the normal frame. |
| `i_tod_prompt_icon_door.png` | 256 x 256 | A buyable door / gate |
| `i_tod_prompt_icon_perk.png` | 256 x 256 | A perk drink (a bottle or can) |
| `i_tod_prompt_icon_pap.png` | 256 x 256 | Pack-a-Punch: a weapon-upgrade machine |
| `i_tod_prompt_icon_power.png` | 256 x 256 | A power switch / lever with a bolt |
| `i_tod_prompt_icon_teleporter.png` | 256 x 256 | A teleporter pad with a beam |
| `i_tod_prompt_icon_altar.png` | 256 x 256 | The upgrade altar: a shrine holding a glowing card |
| `i_tod_prompt_icon_crate.png` | 256 x 256 | An ammo crate with rounds |
| `i_tod_prompt_icon_crown.png` | 256 x 256 | A crown |
| `i_tod_prompt_icon_extract.png` | 256 x 256 | Extraction: an escape craft or beacon calling for pickup |
| `i_tod_prompt_icon_rampage.png` | 256 x 256 | Rampage: a skull with horns or flames, danger |
| `i_tod_prompt_icon_partner_bench.png` | 256 x 256 | NEW. A robot workbench: a table with a wrench and a robot head |
| `i_tod_prompt_icon_partner_part.png` | 256 x 256 | NEW. A robot part: a gear or a mechanical limb |
| `i_tod_prompt_icon_alarm.png` | 256 x 256 | NEW. An alarm: a spinning siren lamp |
| `i_tod_prompt_icon_generic.png` | 256 x 256 | NEW. Fallback for anything else: a hand pressing, or a "use" chevron |

**Every width and height above is a multiple of 4. Keep them exact.** A file at any other
size is rejected by the game's converter.

### The card frame: exact slot positions

Open `reference/slot_map_924x304.png`. The coloured boxes are where the game writes. The
pixel numbers under the card are exact and are the same in your new frame:

| # | Slot | x (px) | y (px) | You draw |
|---|---|---|---|---|
| 1 | Icon well | 8 .. 284 | 4 .. 296 | A dark recessed window with a thin frame, like the round badge's window. Empty inside. |
| 2 | Icon | 60 .. 236 | 68 .. 244 | Nothing. The game places the icon here, inside the well. |
| 3 | Title | 304 .. 904 | 17 .. 63 | A header band behind the title: slightly lighter plate. Empty. |
| 4 | Underline | 284 .. 916 | 66 .. 72 | A thin CYAN neon rule under the header (it was red). |
| 5 | Body | 304 .. 892 | 72 .. 226 | Plain dark plate. Empty. Nothing busy here: this is where text goes. |
| 6 | Divider | 288 .. 912 | 226 .. 228 | A thin steel rule between the body and the footer. |
| 7 | Footer | 304 .. 716 | 228 .. 290 | Plain dark plate. Empty. |
| 8 | Price | 732 .. 908 | 228 .. 290 | Plain dark plate. Empty. May have a faint separate pocket. |

- The outer frame fills the whole 924 x 304 canvas, with a chamfered (cut) corner or two,
  a thin steel frame line and a magenta edge light, matching the round badge and pause menu.
- Keep the TITLE band, BODY, FOOTER and PRICE areas FLAT and DARK. White game text must
  read on them at small size. No texture, no grid, no symbols behind text.
- Everything must sit on the lines above. The game's text boxes do not move.

**The wide frame (1200 x 304).** Identical to the normal frame except the text area is
276 px longer. The icon well stays exactly where it is (x 8..284). Every right-hand
position moves right by 276 px: title band to x 1180, underline to x 1192, body to
x 1168, divider to x 1188, footer to x 992, price to x 1008..1184.

**The locked frame (924 x 304).** The normal frame, identical slot positions, for "not
yet / refused" states such as "POWER REQUIRED" or "SEALED". Make it read as refused at a
glance: the magenta edge light dimmer or broken, the underline a darker magenta, the plate a
little colder. It must NOT look like a hot, active state. The text areas stay flat and
dark.

### The icons

- **Style:** match `reference/i_tod_pm_ico_damage.png`: a flat, bold, WHITE glyph with a
  soft glow. One magenta or cyan neon accent per icon is allowed (a lamp, a bolt, a jewel). No gold, no
  cartoon shading.
- **Size inside the file:** the glyph fills about 80% of the 256 x 256 canvas, centred,
  on a fully transparent background. No plate, frame or circle behind it: the card's
  well is the frame.
- **Readability:** each icon is seen at about 66 px on a 1080p screen. Test every one
  shrunk to 64 px. It must still read as that object.
- **Same objects as today** (`reference/current_icons_BEING_REPLACED.png`), in the new
  style. The four marked NEW are new objects.
- The perk card shows each perk's own colourful logo (`reference/i_tod_perk_jugg.png`)
  in the well instead of an icon. Check your well looks right around it.

### Hard rules

1. Exact filenames and sizes from the table. PNG with transparency.
2. **No text anywhere.** No words, numbers, letters, prices or button names in any file.
   The game draws all of it. (If a decoration needs a letter, don't use one.)
3. The slot positions in the table are exact. Don't move the well, the rules or the
   bands.
4. Text areas (title band, body, footer, price) stay flat and dark.
5. Colours: dark violet-black glass plates, thin violet-steel frames, magenta and cyan neon-tube
   edge light, white glyphs. No red.
6. Every width and height is a multiple of 4.

### Prompts (paste-ready)

**Frames (attach `slot_map_924x304.png`, `target_reference.png`,
`round_badge_as_installed_mock.png`, `i_tod_pm_row.png`, `i_tod_h2_round_badge.png`,
`i_tod_pm_btn_focus.png` for the magenta glow, and `current_card_in_use_BEING_REPLACED.png` to see
where the game's text lands):**
> A 924x304 transparent PNG: an empty HUD interaction card for a dark sci-fi zombie game,
> in the exact style of the attached neon synthwave pause menu and round badge. Dark
> violet-black glass chamfered plate, thin steel frame line, hot magenta edge light. On the left a
> dark recessed square window (x 8..284, y 4..296) with a thin frame, empty. On the
> right: a slightly lighter flat header band (x 304..904, y 17..63), a thin cyan rule
> under it (y 66..72), a flat dark body (y 72..226), a thin steel divider (y 226..228),
> and a flat dark footer row (y 228..290) with a faint separate pocket on its right end
> (x 732..908). All areas empty. No text, no symbols, no grid. Follow the attached slot
> map exactly.

Then the same prompt at 1200x304 with the right-hand areas 276 px longer (wide), and at
924x304 with a dimmed, broken magenta edge light and a colder plate (locked).

**Icons (attach `i_tod_pm_ico_damage.png`, `current_icons_BEING_REPLACED.png`):**
> A 256x256 transparent PNG icon: a flat, bold, WHITE glyph of <OBJECT> with a soft white
> glow, one small magenta accent, centred, filling about 80% of the canvas, in the exact
> style of the attached white glyph. No background, no plate, no text. Must read at 64 px.

### Delivery checklist

- [ ] 17 files, exact names, exact sizes (all multiples of 4).
- [ ] No text or numbers baked into any file.
- [ ] The three frames line up with `slot_map_924x304.png` (overlay them to check).
- [ ] Text areas flat and dark on all three frames.
- [ ] Icons white with at most one magenta accent, transparent background, readable at 64 px.
- [ ] One preview sheet (any size, named `_preview.png`) showing a frame with an icon in
      the well, for a quick look.

### Do NOT

- Do not add words, button names or prices. The game draws them live.
- Do not change any slot position or the canvas sizes.
- Do not put a plate, circle or frame behind the icons.
- Do not use red or the old cartoon style.
- Do not put texture, patterns or symbols behind the text areas.

<!-- PACK:END -->
