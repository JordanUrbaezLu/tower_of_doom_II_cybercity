# 181 — SCOREBOARD V2: the red "Fallen" match scoreboard, every asset it needs

<!-- art-pack
name: scoreboard_v2
refs:
  docs/180_pause_menu_ref/scoreboard_target_reference.png | THE TARGET. The finished scoreboard the user approved. Match it as closely as the rules allow.
  docs/180_pause_menu_ref/sb_component_map.png | The target with every component boxed and labelled with its file letter (A..F). This is how the screen is cut into files.
  docs/180_pause_menu_ref/sb_crop_header.png | 2x close-up: the top panel's header band, round box, YOUR UPGRADES title.
  docs/180_pause_menu_ref/sb_crop_rows.png | 2x close-up: the upgrade rows (wider and shorter than the pause menu's).
  docs/180_pause_menu_ref/sb_crop_face.png | 2x close-up: the zombie face section with MORE ZOMBIES HIGHER STAKES.
  docs/180_pause_menu_ref/sb_crop_table.png | 2x close-up: MATCH SCOREBOARD, the column header strip and the red local-player row.
  docs/180_pause_menu_ref/sb_crop_points.png | 2x close-up: the POINTS capsule at the bottom.
  docs/180_pause_menu_ref/sb_crop_corners.png | 2x close-up: the top-right corner text.
  docs/180_pause_menu_ref/target_reference.png | The PAUSE MENU already built from this same design language. Its pieces are the style to match.
  i_tod_pm_row.png | THE PAUSE MENU ROW CARD, already delivered and in the game. The scoreboard row (C) is this card's WIDER, SHORTER sibling: same materials, well and frame.
  i_tod_pm_panel_left.png | The pause menu's left panel, delivered: the top panel (B) shares its header band, emblem notch, ROUND box, tagline and YOUR UPGRADES title exactly.
  i_tod_pm_backdrop.png | The pause menu's backdrop, delivered: the scoreboard backdrop (A) is its sibling with different corner text.
  i_tod_pm_pip_on.png | The lit level dot, delivered and REUSED on the scoreboard (not part of this pack).
  i_tod_pm_ico_damage.png | One of the 26 white upgrade icons, delivered and REUSED on the scoreboard (not part of this pack).
-->

> **STATUS: REQUESTED 2026-09-26 (user, after the pause menu landed: "the scoreboard
> also needs the same redesign. Get me a new asset request zip on what you need").
> NOTHING INSTALLED, NOTHING BUILT.** `AetheriumScoreboard.lua` is rebuilt on these 8
> files + the pause menu's pips and 26 icons once the drop lands. Same rules as docs/180.

## Repo-facing notes

- The scoreboard is the Tab overlay (`AetheriumScoreboard.lua`, ~1230 lines, built
  ONCE with alpha-toggled states, rows rebuilt per open through `TodBuildUpgradeList`).
  The player table (`#`, NAME, TOTAL POINTS, ELIMINATIONS, CRITICAL KILLS, DOWNS,
  REVIVES) already exists as UIText columns; the redesign keeps every data lane and
  replaces the chrome. The LEVEL column is hidden already (no levelling) and stays out.
- **Row budget** = the pause menu's `TOD_PAUSE_ROWS_CAP` 12 (2 x 6): the scoreboard
  rows go from 3 x 6 to 2 x 6 at ONE fixed size; the lint's scoreboard capacity
  (`TOD_UPG_COLS x TOD_UPG_ROWS_COL`) becomes 2 x 6 = 12 in the same edit. Rows show
  the name, the effect line and the pips only (no activation line, no reset badge) as
  in the target.
- **Reused, not requested:** `i_tod_pm_pip_on / _off / _on_violet`, all 26
  `i_tod_pm_ico_*`, the map emblem.
- **Canvas plan (1280x720):** top panel 28..1201 x 28..425 (art 1536x520 at 0.7637),
  6 rows a column at pitch 40 (row 36 tall = art 1024x112 at 0.3214 -> 329 wide),
  bottom panel 46..1225 x 431..645 (art 1540x280), points capsule 522..758 x 650..701
  (art 480x104 at 0.4917). Player rows 30 tall x up to 4.
- **The multiple-of-4 rule** (build 14): every delivered width and height is a
  multiple of 4 or the converter refuses the image. Every size below is.

## Install (when the drop lands)

`-Inspect`, look at all 8, proofread section 4, check the EMPTY areas, verify sizes
are multiples of 4 (PIL). Copy in, 8 GDT blocks (`compressed high color`) + 8 zone
lines (ping the lead: shared). Rebuild `AetheriumScoreboard.lua` behind
`USE_SCOREBOARD_V2` (old layout kept), `TOD_UPG_COLS 3 -> 2`, retire the
`i_tod_pause_hdr` / `_legend_reset` / plate draws there once the pause menu's old path
is retired too. FULL build (lead-cleared). Proof: 8 fresh content-hash .iwi in the ledger.

<!-- PACK:BEGIN -->

# TOWER OF DOOM II — THE NEW SCOREBOARD (8 files)

We are replacing the in-match scoreboard (the screen the player holds Tab for) with
the design in `reference/scoreboard_target_reference.png`. **That image is the
target.** It is the sibling of the pause menu you already delivered: same red
"Fallen" language, same materials, same frames. `reference/target_reference.png`,
`i_tod_pm_panel_left.png`, `i_tod_pm_row.png` and `i_tod_pm_backdrop.png` are the
delivered pause-menu pieces — **match them exactly**; the scoreboard must look like it
came from the same hand.

As before, the game draws all changing text, numbers and dots itself, so the design
is delivered **in pieces with the changing parts EMPTY**.
`reference/sb_component_map.png` shows the cut, one letter per file.

**The single most important rule: where this brief says EMPTY, leave it empty.**

The level dots and the 26 red upgrade icons are NOT in this pack: the game reuses
the pause menu's (`i_tod_pm_pip_on.png`, `i_tod_pm_ico_damage.png` in `reference/`
show them). Size the row's icon well for a 40 x 40 icon.

---

## 1. What is in the zip

- `reference/scoreboard_target_reference.png` — THE TARGET (1672 x 941).
- `reference/sb_component_map.png` — the target cut into labelled pieces.
- `reference/sb_crop_*.png` — 2x close-ups of each area.
- `reference/target_reference.png` + `i_tod_pm_*.png` — the pause menu and its
  delivered pieces: THE STYLE TO MATCH.
- `typography/` — the game's typeface. **Every baked letter uses it.** The target was
  drawn with a different font: keep its layout, size and colour, set the words in OUR
  face. Our face has no `:` `!` `?` `&` `,` `%`.

---

## 2. Deliverables — exact names, exact sizes, PNG with transparency

Everything outside a panel's own shape is **fully transparent**. **Every width and
height is a multiple of 4** — the game's converter rejects any other size.

| file | size | what it is | baked text | must be EMPTY |
|---|---|---|---|---|
| `i_tod_sb_backdrop.png` | 1920 x 1080 | Full-screen overlay: dark vignette at the edges, red/purple haze and embers, **transparent in the middle**. Sibling of `i_tod_pm_backdrop.png` — same treatment, different words. Top-right: the neon sign **THE DEAD / NEVER REST** (red neon tubes on a dark plate, as in the target, not plain text). | bottom-left **A HIGHER ROUND AWAITS...** (small grey, red rule above); bottom-right **SURVIVE / UPGRADE / DOMINATE** (small grey, stacked, red slash) | everything else; no panels in it |
| `i_tod_sb_panel_top.png` | 1536 x 520 | The whole top panel (box **B**): the header band (emblem notch top-left, TOWER OF DOOM II / ROUND BASED ZOMBIES, the ROUND box, the tagline), the **YOUR UPGRADES** band with its red rule, the empty body, and on the right the **zombie face section** (the face fading into the panel, red eyes, the stacked words). Match the header band to `i_tod_pm_panel_left.png` exactly. | **TOWER OF DOOM II** / **ROUND BASED ZOMBIES** / **/// FIGHT. UPGRADE. SURVIVE. REPEAT. ///** / in the round box only **ROUND** / **YOUR** (white) **UPGRADES** (red) / **MORE / ZOMBIES / HIGHER / STAKES** (small grey, stacked, red rule under) | (1) the emblem spot, x 40..170, y 0..150: dark panel only; (2) the round NUMBER area under the word ROUND; (3) THE BODY x 64..1180, y 190..500: plain dark panel, **no row cards** — the game draws 2 columns x 6 rows there |
| `i_tod_sb_row.png` | 1024 x 112 | ONE upgrade row card (box **C**): the pause row's wider, shorter sibling. Chamfered dark card, thin steel frame, and the **icon well** on the left: a square chamfered tile with a red frame and dark red glow, 92 x 92 px, left edge at x 10, vertically centred. **Everything right of the well (x 120..1010) is EMPTY.** | none | the well's centre and all of x 120..1010 |
| `i_tod_sb_row_violet.png` | 1024 x 112 | The same card for a DARK upgrade: well frame and card edge glow **violet `#B45CFF`**. Pixel-aligned with the plain row. | none | same as above |
| `i_tod_sb_panel_bottom.png` | 1540 x 280 | The whole bottom panel (box **D**): frame, **MATCH SCOREBOARD** title band with its red rule, the tagline on the right, and the **column header strip** (a slightly lighter framed band, y 78..118) with the seven column titles baked in light blue `#4FC3F7`, wide letter spacing, each CENTRED on its column x (below). | **MATCH** (white) **SCOREBOARD** (red) / **// DEATH FUNDS A BRIGHTER TOMORROW.** (small grey, red slashes) / column titles: **#** at x 90, **NAME** at x 277, **TOTAL POINTS** at x 598, **ELIMINATIONS** at x 803, **CRITICAL KILLS** at x 1023, **DOWNS** at x 1224, **REVIVES** at x 1407 | the rows area y 122..272: plain dark panel, **no player rows** — the game stacks up to four there |
| `i_tod_sb_player_row.png` | 1536 x 52 | One player row (box **E**): a thin chamfered dark bar with a faint steel frame. | none | the whole bar — the game writes the seven values on it |
| `i_tod_sb_player_row_local.png` | 1536 x 52 | The same bar for YOUR OWN row: **red neon frame with a red glow**, dark red fill (as the target's row). Pixel-aligned with the plain row. | none | the whole bar |
| `i_tod_sb_points.png` | 480 x 104 | The points capsule (box **F**): a chamfered plate with red edge light. Left third: the yellow **Z points glyph** (as in the target) and the word **POINTS** (small, white, above the value line). | **POINTS** | the right two thirds (x 170..470): the game writes the yellow number there, large |

### Overview (1)

`_overview.png`, 1920 x 1080: **your own pieces assembled** over the backdrop in the
target's layout, with example text typed on and 2 x 6 rows in the body (repeat rows;
use the target's words). It is not used in the game.

**Total: 8 files, plus the overview.**

---

## 3. Every baked word, exactly (proofread against this list)

A: `THE DEAD` · `NEVER REST` · `A HIGHER ROUND AWAITS...` · `SURVIVE` · `UPGRADE` · `DOMINATE`
B: `TOWER OF DOOM II` · `ROUND BASED ZOMBIES` · `FIGHT. UPGRADE. SURVIVE. REPEAT.` ·
`ROUND` · `YOUR` · `UPGRADES` · `MORE` · `ZOMBIES` · `HIGHER` · `STAKES`
D: `MATCH` · `SCOREBOARD` · `DEATH FUNDS A BRIGHTER TOMORROW.` · `#` · `NAME` ·
`TOTAL POINTS` · `ELIMINATIONS` · `CRITICAL KILLS` · `DOWNS` · `REVIVES`
F: `POINTS`

**No other word appears on any file.** The target's "Mod loaded: zm_tod2_cybercity"
corner text is NOT baked (it is not part of the design). Our typeface has no `#`
glyph: draw `#` as two short crossed bars in the same stroke weight as the letters.

---

## 4. Prompts (paste one per group; attach the files named)

**A backdrop** — attach `scoreboard_target_reference.png`, `i_tod_pm_backdrop.png`, `sb_crop_corners.png`, `typography/`:
> Recreate the pause-menu backdrop's sibling for the scoreboard, 1920x1080, transparent
> in the middle: same vignette, haze and embers as the attached `i_tod_pm_backdrop.png`.
> Top-right: the red neon sign THE DEAD / NEVER REST as in the target. Bottom-left: A
> HIGHER ROUND AWAITS... with a red rule above. Bottom-right: SURVIVE / UPGRADE /
> DOMINATE stacked with a red slash. All words in the attached typeface. Nothing else.

**B top panel** — attach `scoreboard_target_reference.png`, `sb_component_map.png`, `sb_crop_header.png`, `sb_crop_face.png`, `i_tod_pm_panel_left.png`:
> Recreate ONLY the top panel of the attached scoreboard as a standalone 1536x520 PNG
> with a transparent outside. Its header band (emblem notch, title, ROUND box,
> tagline) must match the attached pause-menu panel `i_tod_pm_panel_left.png`
> exactly. Keep the YOUR UPGRADES band with its red rule, the grime and red edge
> light, and the zombie face section on the right with MORE / ZOMBIES / HIGHER /
> STAKES. Leave EMPTY: the emblem spot top-left, the round number, and the whole body
> x 64..1180, y 190..500 (plain dark panel, no row cards).

**C rows** — attach `sb_crop_rows.png`, `i_tod_pm_row.png`:
> Draw the attached pause-menu row card's wider, shorter sibling: 1024x112, same
> materials, thin steel frame, and a 92x92 red-framed icon well at x 10, vertically
> centred, with NOTHING written on the card and nothing in the well. Then the same
> card with a violet (#B45CFF) well and edge glow.

**D bottom panel + E player rows** — attach `sb_crop_table.png`, `sb_component_map.png`:
> Draw the bottom panel, 1540x280, transparent outside: frame, MATCH SCOREBOARD title
> with red rule, the tagline on the right, and a framed column-header strip at y
> 78..118 with the seven titles (list attached) centred on the given x positions in
> light blue. The rows area y 122..272 is EMPTY dark panel. Then two player row bars,
> 1536x52 each, with NOTHING written on them: a plain steel-framed bar, and the same
> bar with a red neon frame and glow.

**F points capsule** — attach `sb_crop_points.png`:
> Draw the points capsule, 480x104, transparent outside: chamfered dark plate with red
> edge light, the yellow Z points glyph and the small word POINTS on the left third,
> the right two thirds EMPTY (the game writes the number there).

---

## 5. Delivery checklist

- [ ] 8 PNGs + `_overview.png`, names exactly as above, lowercase.
- [ ] Every size exact, and every width/height a multiple of 4.
- [ ] Transparent outside every panel / row / capsule; the backdrop transparent in the middle.
- [ ] Every EMPTY area empty — no stray word, number, dot, icon or row card.
- [ ] Every baked word from section 3, in OUR typeface, and nothing else; column titles on their x positions.
- [ ] Row twins and player-row twins line up pixel for pixel.
- [ ] The header band of the top panel matches `i_tod_pm_panel_left.png`.
- [ ] `_overview.png` assembled from your own files looks like the target.

## 6. Do NOT

- Do not deliver the whole scoreboard as one picture (only `_overview.png` is that).
- Do not bake any upgrade name, level dot, icon, player name, number or round number.
- Do not redraw our purple skull emblem, the level dots or the 26 icons.
- Do not bake "Mod loaded: ..." anywhere.
- Do not use any font other than the one in `typography/`.

<!-- PACK:END -->
