# 184a — SYNTHWAVE PAUSE MENU: the pause menu redrawn in the neon synthwave theme

<!-- art-pack
name: synthwave_pause_menu
refs:
  docs/184_synthwave_ref/style_board.png | THE STYLE. The new neon synthwave look: palette, tube frames, focus / ready / locked / rampage states. Match this above everything else.
  docs/184_synthwave_ref/world_city_ingame.png | THE WORLD. The game view this UI sits on top of: black towers outlined in neon. The UI must feel like part of it.
  docs/180_pause_menu_ref/target_reference.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). THE TARGET. The finished pause menu the user approved. Match it as closely as the rules allow.
  docs/180_pause_menu_ref/component_map.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). The target with every component boxed and labelled with its file code (A1, C1, E4 ...). This is how the screen is cut into files.
  docs/180_pause_menu_ref/crop_left_header.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). 2x close-up: left panel header, round box, YOUR UPGRADES title (A2).
  docs/180_pause_menu_ref/crop_rows.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). 2x close-up: all ten upgrade rows (C1 frame, D icons, pips).
  docs/180_pause_menu_ref/crop_row_single.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). 2x close-up of ONE row as it looks in game WITH the game's text and pips drawn on it.
  docs/180_pause_menu_ref/example_row_EMPTY_as_delivered.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). What C1 must look like as DELIVERED: the frame and the empty icon well, nothing else.
  docs/180_pause_menu_ref/crop_icons.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). 2x close-up of the ten upgrade icons in their wells (D).
  docs/180_pause_menu_ref/crop_right_header.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). 2x close-up: right panel, title, zombie face, the four icon buttons (A3, B1, E1, E2).
  docs/180_pause_menu_ref/crop_buttons.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). 2x close-up: the five menu buttons, the top one focused (E4, E5, F glyphs).
  docs/180_pause_menu_ref/example_button_EMPTY_as_delivered.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). What E4 must look like as DELIVERED: frame, icon cell, divider, chevron. No icon, no words.
  docs/180_pause_menu_ref/example_button_focus_EMPTY_as_delivered.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). What E5 (focused) must look like as DELIVERED.
  docs/180_pause_menu_ref/crop_legend.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). 2x close-up: the UPGRADE CARDS box (E6).
  docs/180_pause_menu_ref/crop_footer.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). 2x close-up: the bottom strip of the left panel and the corner text (A1, A4).
  docs/180_pause_menu_ref/emblem_ours_in_game.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). OUR map emblem (the purple skull). The game draws it on top of A2. Do NOT redraw it; leave its spot dark.
  docs/180_pause_menu_ref/current_ingame_DO_NOT_COPY.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). The CURRENT pause menu being replaced. For context only. Do not copy its style.
  i_tod_pad_button_a.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). A control glyph the game already draws inside the E6 box (it is not part of your work; shown so you leave room for it).
  i_tod_pad_dpad_left.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). Another control glyph the game draws inside E6.
-->

> **STATUS: REQUESTED 2026-09-26** (user, after seeing the red prompt-card drop: "I kinda want
> a different theme tho" -> chose NEON SYNTHWAVE for the WHOLE UI). NOTHING INSTALLED.
> 20 files. Same names, sizes and slots as 180_pause_menu_v2_art_prompt.md, so the install is a FILE SWAP plus the
> code tints listed in docs/184_synthwave_theme.md. The red set stays installed until the
> synthwave drop lands.

<!-- PACK:BEGIN -->
# Synthwave pause menu: redraw the pause menu in the new neon synthwave theme

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

## Files to deliver (20, exact names and sizes, every size a multiple of 4)

| File | Size (px) |
|---|---|
| `i_tod_pm_backdrop.png` | 1920 x 1080 |
| `i_tod_pm_btn.png` | 1024 x 112 |
| `i_tod_pm_btn_focus.png` | 1024 x 112 |
| `i_tod_pm_footer_flavor.png` | 800 x 40 |
| `i_tod_pm_iconbtn.png` | 324 x 192 |
| `i_tod_pm_iconbtn_focus.png` | 324 x 192 |
| `i_tod_pm_legend_box.png` | 1024 x 216 |
| `i_tod_pm_legend_reset.png` | 800 x 40 |
| `i_tod_pm_panel_left.png` | 1468 x 1196 |
| `i_tod_pm_panel_right.png` | 896 x 1208 |
| `i_tod_pm_pip_off.png` | 64 x 64 |
| `i_tod_pm_pip_on.png` | 64 x 64 |
| `i_tod_pm_pip_on_violet.png` | 64 x 64 |
| `i_tod_pm_reset_mark.png` | 64 x 64 |
| `i_tod_pm_row.png` | 1024 x 200 |
| `i_tod_pm_row_violet.png` | 1024 x 200 |
| `i_tod_pm_timebar.png` | 1024 x 100 |
| `i_tod_pm_title_gameover.png` | 1024 x 248 |
| `i_tod_pm_title_pause.png` | 1024 x 248 |
| `i_tod_pm_title_settings.png` | 1024 x 248 |

**Do NOT redraw:** the white upgrade icons (`i_tod_pm_ico_*`) and the white menu glyphs (`i_tod_pm_gly_*`): 40 files, theme-neutral, the game tints them.

Read the ORIGINAL SPEC below for what each file is, its baked words and its empty areas.
It is correct in every respect except colour: follow it, but colour everything with the
theme above. Where the spec's file list and the list above disagree, the list above wins.


## ORIGINAL SPEC (colours already re-worded for synthwave; if any colour word below still disagrees with the theme above, the theme wins): TOWER OF DOOM II — THE NEW PAUSE MENU (60 files)

We are replacing the game's pause menu with the design in
`reference/target_reference.png`. **That image is the target. Match its look —
frames, materials, colours, glow, scratches, spacing — as exactly as you can.**

But the game cannot use it as one picture. The game draws all the changing text,
numbers and dots itself, on top of your art. So we need the design **cut into
separate pieces**, each piece a separate PNG, with the changing parts left
**EMPTY**. `reference/component_map.png` shows exactly how the target is cut:
every box is labelled with the code of the file you deliver for it.

**The single most important rule: where this brief says EMPTY, leave it empty.**
If you bake a word, a number or a dot into a spot the game writes into, the game
draws its own on top and the screen shows both.

---

### 1. What is in the zip

- `reference/target_reference.png` — THE TARGET (1672 x 941).
- `reference/component_map.png` — the target cut into labelled pieces.
- `reference/crop_*.png` — 2x close-ups of each area of the target.
- `reference/example_row_EMPTY_as_delivered.png`,
  `example_button_EMPTY_as_delivered.png`,
  `example_button_focus_EMPTY_as_delivered.png` — rough mock-ups of how a
  delivered piece looks with its empty areas empty. Deliver clean art, not these
  patched crops.
- `reference/emblem_ours_in_game.png` — our purple skull emblem. The game draws it
  itself. **Do not redraw it.**
- `reference/current_ingame_DO_NOT_COPY.png` — the menu being replaced. Context
  only.
- `reference/i_tod_pad_*.png` — control glyphs the game draws inside the legend
  box. Not your work; shown so you leave room.
- `typography/` — the game's typeface. **Every baked letter uses it** (see the
  TYPOGRAPHY section at the end). The target was drawn with a different font:
  keep its layout, size and colour, but set the words in OUR face.

---

### 2. The look (from the target)

- **Palette.** Near-black blue panels `#140C24`, darker row cards `#0C0716`, thin
  steel-grey frame lines with a faint blue sheen, **hot magenta accents and glow**
  `#FF2BD1` (glow `#FF2BD1`), a little purple haze on the outer frame edges.
  Text colours the game will use on your art: white names `#EEF1F8`, light blue
  effect lines `#7FC8F4`, grey detail lines `#4A3A70`, magenta numbers `#FF2BD1`.
- **Frames.** Chamfered (cut) corners, 1-2 px steel lines, magenta light on one edge
  or corner, subtle grime, scratches and magenta splatter texture in the panel
  corners. Dark zombie silhouettes and magenta cracks faded into the bottom of the
  left panel. The right panel carries the big **zombie face with glowing magenta eyes**
  in its top-right corner, fading into the panel.
- **No live content in any frame.** No upgrade names, no numbers, no dots, no
  button words.

---

### 3. Deliverables — exact names, exact sizes, PNG with transparency

Everything outside a panel's own shape is **fully transparent**. Sizes are exact:
the game places each file by its pixel size. **Every width and height is a multiple
of 4** — the game's converter rejects any other size outright.

#### A. Backdrop and panels (4)

| file | size | what it is | baked text | must be EMPTY |
|---|---|---|---|---|
| `i_tod_pm_backdrop.png` | 1920 x 1080 | Full-screen overlay behind both panels: dark vignette at the edges, faint magenta/purple haze and embers, **transparent in the middle** so the game world shows through. | top-right corner: **THE DEAD / NEVER REST** (small, grey, wide letter spacing, cyan underline stroke). bottom-left corner: **A HIGHER ROUND AWAITS...** (small, grey). | everything else; no panels in it |
| `i_tod_pm_panel_left.png` | 1468 x 1196 | The whole left panel (box **A2**): frame, header band, the ROUND box, the YOUR UPGRADES title band, the big empty body, the bottom band. | **TOWER OF DOOM II** / **ROUND BASED ZOMBIES** / **/// FIGHT. UPGRADE. SURVIVE. REPEAT. ///** (small, grey, cyan slashes) / in the round box only the word **ROUND** / **YOUR** (white) **UPGRADES** (magenta) with its cyan rule / **STRONGER / DEADLIER / FURTHER** (small italic grey, cyan double slash) / bottom right **ZOMBIES MODE // TOWER OF DOOM II** (tiny grey) | (1) the emblem spot, top-left, pixels 100..290 x 0..150 of your file: dark panel only, our skull goes there; (2) the round NUMBER area under the word ROUND; (3) the whole body where the ten rows go (x 70..1450, y 320..1070): plain dark panel, **no row cards**; (4) the bottom-left text slot (x 70..680, y 1100..1145) |
| `i_tod_pm_panel_right.png` | 896 x 1208 | The whole right panel (box **A3**): frame, the zombie face top-right, a thin divider line under the title area, the empty body. | none | the title spot top-left (x 80..600, y 50..185); everything below the divider (buttons, time bar and legend box are separate files) |
| `i_tod_pm_footer_flavor.png` | 800 x 40 | The small strip at the left panel's bottom-left (box **A4**). | **DEATH FUNDS A BRIGHTER TOMORROW** + a magenta **/** | transparent background |

#### B. Title plates (3) — one per menu mode, same design, transparent background

| file | size | big title (white, bold, magenta `//` after it) | subtitle (grey, very wide spacing) |
|---|---|---|---|
| `i_tod_pm_title_pause.png` | 1024 x 248 | **PAUSE MENU //** | **GAME NOT OVER YET** |
| `i_tod_pm_title_gameover.png` | 1024 x 248 | **GAME OVER //** | **RESTART OR WALK AWAY** |
| `i_tod_pm_title_settings.png` | 1024 x 248 | **SETTINGS //** | **TUNE YOUR NIGHTMARE** |

Left-aligned like the target. The three must line up exactly when swapped
(same left edge, same baseline, same size).

#### C. The upgrade rows (7)

| file | size | what it is |
|---|---|---|
| `i_tod_pm_row.png` | 1024 x 200 | ONE row card (box **C1**): chamfered dark card, thin steel frame, and the **icon well** on the left: a square chamfered tile with a magenta frame and deep violet inner glow, 164 x 164 px, left edge at x 14, vertically centred. **EVERYTHING right of the well (x 200..1010) is EMPTY card** — no name, no dots, no text lines. See `example_row_EMPTY_as_delivered.png`. |
| `i_tod_pm_row_violet.png` | 1024 x 200 | The same card for a **DARK** (corrupted, top-rarity) upgrade: identical shape, but the well frame and the card's edge glow are **violet `#7A46FF`** with a faint violet haze. Must line up pixel-for-pixel with the plain row. |
| `i_tod_pm_pip_on.png` | 64 x 64 | A lit level dot: glossy blood-cyan sphere with a soft cyan glow, centred, about 40 px across. |
| `i_tod_pm_pip_off.png` | 64 x 64 | An empty level slot: a thin grey ring, same diameter, dark centre, no glow. |
| `i_tod_pm_pip_on_violet.png` | 64 x 64 | The lit dot in violet `#7A46FF`, same shape as pip_on. |
| `i_tod_pm_reset_mark.png` | 64 x 64 | A small **amber `#FFB020` warning badge** (a triangle with a notch or a cracked chevron, NO letter or `!`). It sits on the corner of an icon well to say "this upgrade is lost when your class tier goes up". Must read at 16 x 16. |
| `i_tod_pm_legend_reset.png` | 800 x 40 | A strip that explains the badge: the badge on the left, then **RESETS WHEN YOUR CLASS TIER GOES UP** (small grey, badge amber). Transparent background. It replaces A4 in the same slot when needed, so give it the same height and left edge. |

#### D. Upgrade icons (26) — `128 x 128`, WHITE glyph on transparent

Same style as the ten icons in the target (`crop_icons.png`): one bold, simple,
flat symbol with a soft glow, filling about 70% of the square, centred. **Pure
white / light grey only** — the game colours them magenta (or violet). No frame, no
tile, no background (the row's well is the tile). Must read at 40 x 40.

| file | symbol |
|---|---|
| `i_tod_pm_ico_damage.png` | three bullets standing side by side (as in the target) |
| `i_tod_pm_ico_dr.png` | a starburst impact (as in the target) |
| `i_tod_pm_ico_bounty.png` | a skull (as in the target) |
| `i_tod_pm_ico_luck.png` | a four-leaf clover (as in the target) |
| `i_tod_pm_ico_tier.png` | a star over stacked chevrons (as in the target) |
| `i_tod_pm_ico_summonpower.png` | a snarling demon/hound head (as in the target) |
| `i_tod_pm_ico_soulbeam.png` | a spiral vortex (as in the target) |
| `i_tod_pm_ico_perkslots.png` | a soda bottle / can with a star on it (as in the target) |
| `i_tod_pm_ico_riotshield.png` | a shield (as in the target) |
| `i_tod_pm_ico_soulbomb.png` | a round bomb with a lit fuse (as in the target) |
| `i_tod_pm_ico_grapple.png` | a grappling hook with a short rope |
| `i_tod_pm_ico_retriever.png` | a curved throwing axe / tomahawk with a return arc |
| `i_tod_pm_ico_pellets.png` | a shotgun shell with pellets spreading from it |
| `i_tod_pm_ico_c4.png` | a C4 brick with a blinking dot and wires |
| `i_tod_pm_ico_cluster.png` | one grenade bursting into four small bomblets |
| `i_tod_pm_ico_knifespeed.png` | a clenched fist with speed lines |
| `i_tod_pm_ico_bash.png` | a sword blade dashing forward with motion streaks |
| `i_tod_pm_ico_gravsmash.png` | a fist slamming down, a shockwave ring on the ground |
| `i_tod_pm_ico_chainlightning.png` | a lightning bolt forking into three |
| `i_tod_pm_ico_fireblast.png` | a fireball |
| `i_tod_pm_ico_iceshatter.png` | a shattering ice crystal |
| `i_tod_pm_ico_blink.png` | a figure dashing out of a teleport ring |
| `i_tod_pm_ico_archmage.png` | a wizard hat with a star |
| `i_tod_pm_ico_mysticalhands.png` | an open hand with a glowing sigil above it |
| `i_tod_pm_ico_healingaura.png` | a cross inside a soft ring |
| `i_tod_pm_ico_generic.png` | an upward arrow inside a hexagon (used for any upgrade without its own icon) |

#### E. Right-panel frames (6)

| file | size | what it is | must be EMPTY |
|---|---|---|---|
| `i_tod_pm_iconbtn.png` | 324 x 192 | One square-ish settings button (box **E1**): dark glassy tile, thin steel frame, faint blue light on the bottom edge. | the centre: NO icon (the game draws it) |
| `i_tod_pm_iconbtn_focus.png` | 324 x 192 | The same button while selected: frame and glow go **magenta**, like the focused menu button. Lines up with E1. | the centre |
| `i_tod_pm_timebar.png` | 1024 x 100 | The game-time bar (box **E3**): thin framed strip, **GAME TIME** baked on the left (grey, wide spacing, NO colon). | the right half, where the magenta time goes |
| `i_tod_pm_btn.png` | 1024 x 112 | One menu button (box **E4**): chamfered dark bar, thin steel frame, an **icon cell** on the left (x 0..180) ended by a thin vertical divider, and a grey **`>` chevron** baked at the right end. | the icon cell's centre and the whole label area (x 200..930). See `example_button_EMPTY_as_delivered.png` |
| `i_tod_pm_btn_focus.png` | 1024 x 112 | The same button selected (box **E5**): bright **magenta neon frame with a strong magenta glow**, deep violet fill, chevron white. Lines up with E4. | same as E4 |
| `i_tod_pm_legend_box.png` | 1024 x 216 | The bottom box (box **E6**): framed box with magenta corner light, a **fanned deck of cards** icon on the left, **UPGRADE CARDS** (light blue `#97C7F8`), a thin vertical divider near the right, and in the right column **SAME / MAP / DIFFERENT / NIGHTMARE** (small grey, stacked). | the control row under UPGRADE CARDS (x 190..800, y 105..190): the game puts its own button glyphs and words there |

#### F. Menu glyphs (14) — `128 x 128`, WHITE glyph on transparent

Same style as the icons in the target's four top buttons and five menu buttons:
flat, clean, simple, filling about 60% of the square. White only — the game tints
them grey-blue, and magenta when selected. Must read at 20 x 20.

| file | symbol |
|---|---|
| `i_tod_pm_gly_graphics.png` | a monitor (as in the target) |
| `i_tod_pm_gly_audio.png` | a speaker with sound waves (as in the target) |
| `i_tod_pm_gly_controls.png` | a mouse with a small gear (as in the target) |
| `i_tod_pm_gly_settings.png` | a gear (as in the target) |
| `i_tod_pm_gly_return.png` | three slanted slashes `///` (as on RETURN TO GAME in the target) |
| `i_tod_pm_gly_restart.png` | a circle with four tick marks, a target (as in the target) |
| `i_tod_pm_gly_camera.png` | a person's head and shoulders (as on SWITCH TO THIRD PERSON) |
| `i_tod_pm_gly_leave.png` | a door with an arrow leaving it (as on LEAVE GAME) |
| `i_tod_pm_gly_voice.png` | a microphone |
| `i_tod_pm_gly_network.png` | four rising signal bars |
| `i_tod_pm_gly_safearea.png` | four corner brackets framing an empty rectangle |
| `i_tod_pm_gly_content.png` | an eye |
| `i_tod_pm_gly_credits.png` | a star |
| `i_tod_pm_gly_back.png` | a left-pointing arrow |

#### G. Overview (1)

`_overview.png`, 1920 x 1080: **your own pieces assembled** over the backdrop in
the target's layout, with example text typed on (use the target's words). This
is how you prove the pieces fit. It is not used in the game.

**Total: 4 + 3 + 7 + 26 + 6 + 14 = 60 files, plus the overview.**

---

### 4. Every baked word, exactly (proofread against this list)

A2: `TOWER OF DOOM II` · `ROUND BASED ZOMBIES` · `FIGHT. UPGRADE. SURVIVE. REPEAT.` ·
`ROUND` · `YOUR` · `UPGRADES` · `STRONGER` · `DEADLIER` · `FURTHER` ·
`ZOMBIES MODE // TOWER OF DOOM II`
A1: `THE DEAD` · `NEVER REST` · `A HIGHER ROUND AWAITS...`
A4: `DEATH FUNDS A BRIGHTER TOMORROW`
B: `PAUSE MENU //` · `GAME NOT OVER YET` · `GAME OVER //` · `RESTART OR WALK AWAY` ·
`SETTINGS //` · `TUNE YOUR NIGHTMARE`
C7: `RESETS WHEN YOUR CLASS TIER GOES UP`
E3: `GAME TIME`
E6: `UPGRADE CARDS` · `SAME` · `MAP` · `DIFFERENT` · `NIGHTMARE`

**No other word appears on any file.** Note the target says "ZOMBIER MODE": that
is a typo, write `ZOMBIES MODE`. The target writes "GAME TIME:"; our typeface has
no colon, so it is `GAME TIME`.

---

### 5. Prompts (paste one per group; attach the files named)

**A2 left panel** — attach `target_reference.png`, `component_map.png`,
`crop_left_header.png`, `crop_footer.png`, `emblem_ours_in_game.png`, `typography/`:
> Recreate ONLY the left panel (box A2) of the attached pause-menu design as a
> standalone 1468x1196 PNG with a transparent outside. Keep its frame, header
> band, round box, YOUR UPGRADES band, bottom band, grime, magenta corner light and
> faded zombie silhouettes exactly as in the target. Set the listed words in the
> attached typeface. Leave EMPTY: the emblem spot top-left (dark panel, our skull
> is drawn there), the number area of the round box, the entire body where the
> upgrade rows go (plain dark panel, no cards), and the bottom-left text slot.

**A3 right panel** — attach `target_reference.png`, `component_map.png`, `crop_right_header.png`:
> Recreate ONLY the right panel (box A3) as a 896x1208 PNG with a transparent
> outside: frame, magenta edge light, the zombie face with glowing magenta eyes in the
> top-right corner fading into the panel, and the thin divider under the title
> area. NO title text, NO buttons, NO time bar, NO legend box — those are
> separate files. Everything below the divider is plain dark panel.

**C row + pips + badge** — attach `crop_rows.png`, `crop_row_single.png`, `example_row_EMPTY_as_delivered.png`:
> Draw ONE empty upgrade row card, 1024x200, exactly like the rows in the
> attached design but with NOTHING written on it: the chamfered card, thin steel
> frame, and the square magenta-framed icon well on the left (164x164 at x 14,
> vertically centred) with no icon inside. Then the same card with a violet
> (#7A46FF) well and edge glow. Then the dots at 64x64: glossy cyan lit dot, grey
> empty ring, violet lit dot. Then a small amber warning badge with no letters.

**D icons** — attach `crop_icons.png`, `crop_rows.png`:
> Draw 26 icons, each 128x128, transparent background, pure WHITE flat glyph with
> a soft white glow, same weight and simplicity as the magenta icons in the attached
> rows (list attached). No tile, no frame, no colour. Each must be readable
> shrunk to 40x40.

**E frames** — attach `crop_right_header.png`, `crop_buttons.png`, `crop_legend.png`, the two `example_button_*` files, and `i_tod_pad_button_a.png` + `i_tod_pad_dpad_left.png` (the glyphs the game puts in the legend's empty control row — size that row for them):
> Draw the right panel's parts as separate PNGs at the exact sizes listed: the
> settings button tile (normal + magenta selected) with NO icon; the GAME TIME bar
> with only the words GAME TIME; the menu button bar (normal + magenta neon selected)
> with the empty icon cell, divider and chevron but NO icon and NO words; the
> UPGRADE CARDS box with the card-fan icon, its title and the SAME MAP DIFFERENT
> NIGHTMARE column, and its control row left EMPTY.

**F glyphs** — attach `crop_right_header.png`, `crop_buttons.png`:
> Draw 14 menu glyphs, 128x128, transparent, pure WHITE, flat, the same style as
> the icons in the attached settings buttons and menu buttons (list attached).
> Each must be readable at 20x20.

---

### 6. Delivery checklist

- [ ] 60 PNGs + `_overview.png`, names exactly as above, all lowercase.
- [ ] Every size exact to the pixel.
- [ ] Transparent outside every panel / frame / glyph; the backdrop transparent in the middle.
- [ ] Every EMPTY area empty — no stray word, number, dot or icon.
- [ ] Every baked word from section 4, spelled exactly, in OUR typeface, and nothing else.
- [ ] D and F are white-only glyphs, no colour, no tile.
- [ ] Normal / focused / dark twins line up pixel for pixel (row + row_dark, iconbtn + focus, btn + focus, the three titles).
- [ ] `_overview.png` assembled from your own files looks like the target.

### 7. Do NOT

- Do not deliver the whole menu as one picture (only `_overview.png` is that, and the game does not use it).
- Do not bake any upgrade name, number, level dot, button label, time or round number.
- Do not redraw our purple skull emblem.
- Do not colour the D or F glyphs.
- Do not use any font other than the one in `typography/`, and no characters it lacks (`:` `!` `?` `&` `,` `%`).
- Do not copy the style of `current_ingame_DO_NOT_COPY.png`.


<!-- PACK:END -->
