# 184c — SYNTHWAVE HUD: the HUD redrawn in the neon synthwave theme

<!-- art-pack
name: synthwave_hud
refs:
  docs/184_synthwave_ref/style_board.png | THE STYLE. The new neon synthwave look: palette, tube frames, focus / ready / locked / rampage states. Match this above everything else.
  docs/184_synthwave_ref/world_city_ingame.png | THE WORLD. The game view this UI sits on top of: black towers outlined in neon. The UI must feel like part of it.
  docs/182_hud_ref/proposed_layout_mock.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). THE LAYOUT. A wireframe of the new HUD over a real in-game view at 1080p: where every piece sits and what the game draws live. It is a PLACEMENT sketch, not the look - the look comes from the menus below.
  docs/180_pause_menu_ref/target_reference.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). THE STYLE. The approved pause menu. The HUD must read as the same product: same dark chamfered plates, thin steel frames, hot magenta edge light, same icon style.
  docs/182_hud_ref/scoreboard_as_delivered_overview.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). THE STYLE, second example: the delivered scoreboard.
  docs/182_hud_ref/current_hud_art_BEING_REPLACED.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). The CURRENT HUD art (the old cyan look). Every piece here is replaced. Shown so you know what each new file takes over from - do NOT copy its style.
  i_tod_pm_row.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). Delivered pause-menu row card: the plate material, frame weight and magenta edge light to match.
  i_tod_pm_btn_focus.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). Delivered focused button: THE magenta glow to match for every "ready / active" twin in this pack.
  i_tod_pm_iconbtn.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). Delivered icon tile: the tile material to match for the ability tiles.
  i_tod_pm_pip_on.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). Delivered lit dot: the magenta light quality to match.
  i_tod_pm_ico_damage.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). Delivered WHITE glyph: the exact icon style (flat, bold, white, soft glow) for every glyph in this pack.
  docs/182_hud_ref/scoreboard_points_capsule.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). Delivered scoreboard points capsule: its yellow Z points glyph is the one to redraw alone for the HUD.
  i_tod_class_medallion_necromancer.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). The CLASS MEDALLION the game shows beside the health bar. KEPT as is: the new ring frames it.
  i_tod_hud_gun_mp7.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). A CURRENT gun silhouette (old style), for the optional gun-icon restyle in section G.
  i_tod_hud_off_hook.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). A CURRENT ability icon (old style, the Archer's grapple): section F redraws all 14 of these as white glyphs.
  i_tod_perk_jugg.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). A perk icon. KEPT as is: the new perk socket frames it.
  i_tod_pu2_max_ammo.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). A power-up icon. KEPT as is.
  i_tod_hud_pap_2.png | LAYOUT ONLY (old red style - copy the shapes and positions, NOT the colours). The Pack-a-Punch tier glyph. KEPT as is: the new PaP tile frames it.
  i_tod_h2_round_badge.png | LAYOUT ONLY. The CURRENT round badge (red style): its SHAPE and number window are kept exactly.
  i_tod_h2_luck_plate.png | LAYOUT ONLY. The CURRENT luck plate (red style): its SHAPE and channel are kept exactly.
preview: 1280x720
-->

> **STATUS: REQUESTED 2026-09-26** (user, after seeing the red prompt-card drop: "I kinda want
> a different theme tho" -> chose NEON SYNTHWAVE for the WHOLE UI). NOTHING INSTALLED.
> 23 files. Same names, sizes and slots as 182_hud_v2_art_prompt.md, so the install is a FILE SWAP plus the
> code tints listed in docs/184_synthwave_theme.md. The red set stays installed until the
> synthwave drop lands.

<!-- PACK:BEGIN -->
# Synthwave HUD: redraw the HUD in the new neon synthwave theme

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

## Files to deliver (23, exact names and sizes, every size a multiple of 4)

| File | Size (px) |
|---|---|
| `i_tod_h2_gauge_down.png` | 48 x 48 |
| `i_tod_h2_gauge_seg_off.png` | 40 x 24 |
| `i_tod_h2_gauge_spire.png` | 64 x 900 |
| `i_tod_h2_gauge_tower.png` | 64 x 900 |
| `i_tod_h2_gauge_you.png` | 48 x 48 |
| `i_tod_h2_gun_plate.png` | 1056 x 288 |
| `i_tod_h2_hp_frame.png` | 544 x 48 |
| `i_tod_h2_luck_off.png` | 76 x 48 |
| `i_tod_h2_luck_on.png` | 76 x 48 |
| `i_tod_h2_medallion_ring.png` | 256 x 256 |
| `i_tod_h2_perk_socket.png` | 128 x 128 |
| `i_tod_h2_points.png` | 128 x 128 |
| `i_tod_h2_shield_frame.png` | 544 x 24 |
| `i_tod_h2_tile.png` | 184 x 128 |
| `i_tod_h2_tile_pap.png` | 184 x 128 |
| `i_tod_h2_tile_ready.png` | 184 x 128 |
| `i_tod_h2_toast.png` | 848 x 196 |
| `i_tod_h2_round_badge.png` | 192 x 192 |
| `i_tod_h2_round_badge_rampage.png` | 192 x 192 |
| `i_tod_h2_luck_plate.png` | 944 x 240 |
| `i_tod_h2_luck_plate_rampage.png` | 944 x 240 |

**These four files are NEW since the spec below was written. Their spec is here, and it replaces the spec's `i_tod_h2_status` / `i_tod_h2_status_rampage` rows (those two files no longer exist; do not draw them):**

| File | Size (px) | What it is |
|---|---|---|
| `i_tod_h2_round_badge.png` | 192 x 192 | The ROUND badge, top-left of the screen (a pointed shield shape, see `i_tod_h2_round_badge.png` in reference/). Baked word **ROUND** in a small tab at the top. EMPTY number window at x 38..153, y 60..123: the game draws the round number there. Replaces the round box of the old status plate. |
| `i_tod_h2_round_badge_rampage.png` | 192 x 192 | The same badge while RAMPAGE mode is on: identical shape and window, hot magenta frame with a sunset-orange inner line, and a tiny baked **RAMPAGE** tag under the window. |
| `i_tod_h2_luck_plate.png` | 944 x 240 | The LUCK plate beside the badge. Baked clover glyph + word **LUCK** at top-left. EMPTY recessed channel at x 64..904, y 132..204: the game draws ten luck segments in it. (It is the old status plate with its round box removed.) |
| `i_tod_h2_luck_plate_rampage.png` | 944 x 240 | The same luck plate while RAMPAGE is on: identical geometry, hot magenta frame, sunset inner line, faint embers, tiny baked **RAMPAGE** tag top-right. |

**Do NOT redraw:** the 22 white pieces (ability icons `i_tod_h2_ab_*`, gauge `i_tod_h2_gauge_seg`, `_seg_hub`, `_boss`, the health and shield fills, `i_tod_h2_shield`, `_shield_broken`, `_downed`): theme-neutral, the game tints them.

Read the ORIGINAL SPEC below for what each file is, its baked words and its empty areas.
It is correct in every respect except colour: follow it, but colour everything with the
theme above. Where the spec's file list and the list above disagree, the list above wins.


## ORIGINAL SPEC (colours already re-worded for synthwave; if any colour word below still disagrees with the theme above, the theme wins): TOWER OF DOOM II — THE NEW IN-MATCH HUD (43 files, + 42 optional)

The HUD is what the player looks at for the whole match, so this is the most important
pack in the set. We are replacing the current HUD (the old cyan look,
`reference/current_hud_art_BEING_REPLACED.png`) with one that matches the new pause
menu and scoreboard you delivered: **the same dark, minimal, neon synthwave cyber
style.**

**There is no finished target image this time. The layout is ours; the look is yours.**
- `reference/proposed_layout_mock.png` is a WIREFRAME of the new HUD over a real game
  view: it shows WHERE each piece sits and how big it is. Its drawing is a placeholder.
- `reference/target_reference.png` (the pause menu) and
  `reference/scoreboard_as_delivered_overview.png` are the LOOK: plate material,
  chamfered corners, thin steel frames, magenta edge light, the white-glyph icon style.

**The brief in one line: MINIMAL AND DARK.** The HUD sits over a bright, busy neon city
for an entire match. Every plate is dark and slightly translucent, thin, low and small;
magenta light is an ACCENT (an edge, a glow on what is ready), never a fill. If a piece
looks busy at its on-screen size, it is wrong. Less decoration than the menus, not more.

**The map's story matters for one piece:** players spawn at the TOP of a tower (a
crown) and fight their way DOWN, floor by floor. The progress gauge (section C) must
read as a DESCENT: crown on top, ground at the bottom.

As with the menus, the game draws every changing number, word, dot and fill itself,
so the pieces are delivered **with the changing parts EMPTY**, and bars / segments /
glyphs are delivered **WHITE** so the game can colour them.

---

### 1. What is in the zip

- `reference/proposed_layout_mock.png` — the layout wireframe (1920 x 1080).
- `reference/target_reference.png`, `scoreboard_as_delivered_overview.png` — the style.
- `reference/i_tod_pm_*.png` — delivered menu pieces: plate, focused glow, tile, lit
  dot, and one WHITE glyph (`i_tod_pm_ico_damage.png`) = THE icon style for this pack.
- `reference/scoreboard_points_capsule.png` — its yellow Z points glyph.
- `reference/current_hud_art_BEING_REPLACED.png` and the `i_tod_hud_*` / `i_tod_perk_*`
  / `i_tod_pu2_*` / medallion files — current art. The medallion, perk icons, power-up
  icons and PaP glyph are KEPT and drawn inside your new frames; the rest is replaced.
- `typography/` — the game's typeface. **Every baked letter uses it.**
- `preview_onscreen_1280x720/` — the references at game-canvas size.

---

### 2. Deliverables — exact names, exact sizes, PNG with transparency

Everything outside a piece's own shape is **fully transparent**. **Every width and
height is a multiple of 4** — the game rejects any other size. "WHITE" means pure
white / light grey only, no colour (the game tints it). The canvas size is what it
covers on a 1280 x 720 screen (x1.5 at 1080p) — judge every piece at that size.

#### A. The status plate, top-left (2) — ROUND + LUCK in one piece

| file | size | canvas | what it is | baked | EMPTY |
|---|---|---|---|---|---|
| `i_tod_h2_status.png` | 1280 x 240 | 320 x 60 | Low chamfered dark plate, magenta edge light along the top, thin steel frame. LEFT: a small framed ROUND box (x 32..336). RIGHT: the LUCK slot - a thin recessed channel (x 400..1240, y 132..204) the luck segments sit in, with a small clover glyph and the word LUCK above it. | **ROUND** (small, grey, top of the box) · **LUCK** (small, light grey) | the round NUMBER area inside the box (y 80..224); the luck channel itself (the game fills it) |
| `i_tod_h2_status_rampage.png` | 1280 x 240 | 320 x 60 | The SAME plate while RAMPAGE mode is switched on: identical geometry, but the edge light runs hot along the whole frame, faint embers, and a tiny tag in the top-right corner. | same + **RAMPAGE** (tiny, magenta, top-right corner) | same |

#### B. Luck segments (4) — the game draws ten of these in the channel

| file | size | canvas | what it is |
|---|---|---|---|
| `i_tod_h2_luck_on.png` | 76 x 48 | 19 x 12 | One LIT segment: a slanted parallelogram, **amber-gold `#FFC428`** with a soft glow. |
| `i_tod_h2_luck_off.png` | 76 x 48 | 19 x 12 | The empty slot: same shape, dark, thin grey edge, no glow. |

#### C. The DESCENT gauge, right edge (8)

A tall thin rail down the right edge of the screen (canvas 32 x 450, x 1232..1264, y 110..560).

| file | size | canvas | what it is | EMPTY |
|---|---|---|---|---|
| `i_tod_h2_gauge_tower.png` | 64 x 900 | 32 x 450 | The rail for the main tower: dark slim track, thin steel frame. **Top cap (y 0..72): a small gold CROWN glyph** (simple, flat, readable at 30 px) — where the players start. **Bottom cap (y 828..900): a flat GROUND plate** (a heavy base line with a tiny street / foundation mark) — where they are heading. A faint downward chevron etched in the track near the top says "descend". | the track between the caps (y 76..824): dark only, the game draws the floor segments there |
| `i_tod_h2_gauge_spire.png` | 64 x 900 | 32 x 450 | The rail for the bonus spire (after the tower is beaten, players climb a second tower UP): same rail, **top cap = a jagged magenta SPIRE PEAK glyph**, bottom cap = the same flat base plate, the etched chevron pointing UP. | same |
| `i_tod_h2_gauge_seg.png` | 40 x 24 | 20 x 12 | One floor segment, lit: a short bar with chamfered ends, **WHITE** with a soft glow (the game tints it per district: cyan / green / orange / gold / red). | — |
| `i_tod_h2_gauge_seg_hub.png` | 56 x 24 | 28 x 12 | The wider segment for a lounge / hub floor: same, wider, with a tiny notch on each end. **WHITE**. | — |
| `i_tod_h2_gauge_seg_off.png` | 40 x 24 | 20 x 12 | An unreached floor: same shape as the lit segment, dark, thin grey edge. | — |
| `i_tod_h2_gauge_you.png` | 48 x 48 | 12 x 12 | "YOU ARE HERE": a small solid **magenta** chevron pointing RIGHT (at the rail), soft magenta glow. | — |
| `i_tod_h2_gauge_down.png` | 48 x 48 | 12 x 12 | A teammate is DOWN on this floor: a small **magenta** cross in a ring. | — |
| `i_tod_h2_gauge_boss.png` | 48 x 48 | 12 x 12 | A BOSS is on this floor: a tiny horned skull, **WHITE** (the game tints it). | — |

#### D. The player readout, bottom-left (9) — NO plate behind it

The player HUD is deliberately shell-less: medallion, name, bars and points float on
the screen. These are the only pieces.

| file | size | canvas | what it is |
|---|---|---|---|
| `i_tod_h2_hp_frame.png` | 544 x 48 | 136 x 12 | The HEALTH bar frame: a thin chamfered frame divided into **15 equal cells** by hairline separators, steel grey, a tiny cyan tick at the left end. The inside of every cell is transparent. |
| `i_tod_h2_hp_fill.png` | 544 x 48 | 136 x 12 | The fill that sits UNDER the frame: one solid strip, **WHITE**, exactly the frame's inner area (the game tints it and wipes it left-to-right with health; it also draws it dark as the empty track). |
| `i_tod_h2_shield_frame.png` | 544 x 24 | 136 x 6 | The RIOT SHIELD bar frame, above the health bar: same style, half height, no cells, a tiny shield notch at the left end. |
| `i_tod_h2_shield_fill.png` | 544 x 24 | 136 x 6 | Its fill: one solid strip, **WHITE**, the frame's inner area. |
| `i_tod_h2_points.png` | 128 x 128 | 16 x 16 | The points glyph: the **yellow Z** from the scoreboard capsule, redrawn alone, bold, readable at 16 px. |
| `i_tod_h2_downed.png` | 128 x 128 | 24 x 24 | DOWNED marker: a cracked skull over a cross, **WHITE** (the game tints it red). |
| `i_tod_h2_shield.png` | 128 x 128 | 20 x 20 | Riot shield held: a riot shield front view with a view slot, **WHITE**. |
| `i_tod_h2_shield_broken.png` | 128 x 128 | 20 x 20 | Riot shield broken / recharging: the same shield split by a crack, **WHITE**. |
| `i_tod_h2_medallion_ring.png` | 256 x 256 | 56 x 56 | A thin chamfered octagon RING that frames the class medallion (the medallion sits inside at 84% of this size): steel grey with magenta light on its lower-left edge. **The whole inside is transparent.** |

#### E. Gun, tiles, perks, toast (6)

| file | size | canvas | what it is | baked | EMPTY |
|---|---|---|---|---|---|
| `i_tod_h2_gun_plate.png` | 1056 x 288 | 264 x 72 | The gun plate, bottom-right: ONE low chamfered dark plate, magenta edge light along the top and a short cyan tick at the right end, thin steel frame. A faint recessed well on the left for the gun silhouette (x 24..392, y 96..264). | none | the well; the weapon-name strip along the top (x 420..1032, y 16..84); the ammo area (x 420..1032, y 96..272) — the game writes the clip big and the reserve small there |
| `i_tod_h2_tile.png` | 184 x 128 | 46 x 32 | One ability tile (tactical / lethal): small chamfered dark tile, thin steel frame. | none | the centre (the game draws the white ability glyph and the charge count) |
| `i_tod_h2_tile_ready.png` | 184 x 128 | 46 x 32 | The same tile when the ability is READY: magenta neon frame + magenta glow, like `i_tod_pm_btn_focus.png`. Pixel-aligned with the plain tile. | none | the centre |
| `i_tod_h2_tile_pap.png` | 184 x 128 | 46 x 32 | The same tile for the Pack-a-Punch badge: a thin **gold** frame instead of steel. | none | the centre (the game draws the PaP chevrons) |
| `i_tod_h2_perk_socket.png` | 128 x 128 | 32 x 32 | A perk socket: tiny chamfered dark square, thin steel frame, faint magenta corner tick. The existing perk icons are drawn inside. | none | the centre |
| `i_tod_h2_toast.png` | 848 x 196 | 212 x 49 | The power-up pickup toast (slides in over the power-up row for 3 s): low chamfered dark plate, **gold** edge light on top, a round icon well on the left (x 12..184). | none | the well and the name area (x 200..836) |

#### F. Ability glyphs (14) — `128 x 128`, WHITE, same style as `i_tod_pm_ico_damage.png`

Flat, bold, simple, soft white glow, filling ~70% of the square, readable at 24 x 24.
They replace the current coloured ability icons one for one.

| file | symbol (the ability) |
|---|---|
| `i_tod_h2_ab_hook.png` | a grappling hook on a short taut rope (Archer: GRAPPLE) |
| `i_tod_h2_ab_axe.png` | a curved throwing axe with a return arc (Archer: HELL'S RETRIEVER) |
| `i_tod_h2_ab_bash.png` | a blade dashing forward with streaks (Warrior: BASH) |
| `i_tod_h2_ab_smash.png` | a fist slamming down into a ground shockwave (Warrior: GRAVITY SMASH) |
| `i_tod_h2_ab_cluster.png` | a grenade bursting into four small bomblets (Breacher: CLUSTER) |
| `i_tod_h2_ab_c4.png` | a C4 brick with a blinking dot (Breacher: STICKY C4) |
| `i_tod_h2_ab_summon.png` | a raised hand with a spirit rising from it (Necromancer: SUMMON) |
| `i_tod_h2_ab_soul_bomb.png` | a skull-shaped bomb with a wisp fuse (Necromancer: SOUL BOMB) |
| `i_tod_h2_ab_blink.png` | a figure dashing out of a teleport ring (Mage: BLINK) |
| `i_tod_h2_ab_heal.png` | a cross inside a soft ring (Mage: HEALING AURA) |
| `i_tod_h2_ab_frag.png` | a frag grenade (the standard lethal) |
| `i_tod_h2_ab_monkey.png` | a cymbal monkey toy (the standard tactical) |
| `i_tod_h2_ab_spider.png` | a spider-web grenade (Widow's Wine lethal) |
| `i_tod_h2_ab_spider_phd.png` | the same web grenade with a small blast flash (Widow's Wine + PhD) |

#### G. OPTIONAL — gun silhouettes restyled (42) — `288 x 132`, may come in a later drop

The current gun icons (`i_tod_hud_gun_mp7.png` is one) are the old style. If you have
capacity, redraw all 42 in the new style: a side-on silhouette, flat **steel-light
grey `#D4D9E4`** with ONE thin magenta accent line along the barrel / edge, no outline
glow, filling the frame the same way the current ones do. **Same filenames as today**
(so they drop straight in): `i_tod_hud_gun_` + `ak47, amp63, amp63_akimbo, axe, bat,
blade, bow, bulldog, crossbow, enfield, executioner, executioner_akimbo, firebow,
fist, gauntlet, gift, greatsword, hk21, katana, krig6, launcher, mac10, magnum,
minigun, mog12, mozambique, mp5, mp7, mr6, nailgun, peacekeeper, rem870, rk7, sg12,
shield, skull, spas12, staff1, staff2, staff3, stoner63, udm`. The current file of
each name shows which weapon it is. Skip this section rather than rush it.

#### H. Overview (1)

`_overview.png`, 1920 x 1080: **your own pieces assembled** over
`proposed_layout_mock.png`'s game view in its layout, with example numbers typed on
(ROUND 12, LUCK 6 of 10, FLOOR 41 with 9 floors lit from the top, 150 HP, 4250 points,
32 / 128 ammo, two ability tiles with one READY). It is not used in the game — it is
how you prove the HUD is minimal and reads at size.

**Total: A 2 + B 4 + C 8 + D 9 + E 6 + F 14 = 43 files (+ G 42 optional) + overview.**

---

### 3. Colour and light rules

- Plates: near-black blue `#0C0716` at about **85% opacity** (the world shows faintly
  through), thin steel frame `#4A3A70`, magenta edge light `#FF2BD1` as an accent.
- READY / ACTIVE = MAGENTA lit tube; FOCUS = CYAN lit tube. Gold only for the PaP
  tile and the toast. Amber-gold only for luck.
- WHITE pieces (segments, fills, glyphs): pure white/light grey, soft glow, **no colour**.

### 4. Every baked word, exactly

A: `ROUND` · `LUCK` · `RAMPAGE` (rampage plate only). **No other word appears on any file.**

---

### 5. Prompts (paste one per group; attach the files named)

**A + B status and luck** — attach `proposed_layout_mock.png`, `target_reference.png`, `i_tod_pm_row.png`, `typography/`:
> Draw the HUD's top-left status plate, 1280x240, transparent outside, in the exact
> material of the attached pause menu: a low chamfered dark plate at ~85% opacity,
> thin steel frame, magenta edge light along the top. Left: a small framed box with the
> word ROUND at its top and its number area EMPTY. Right: the word LUCK and a small
> clover glyph above a thin recessed EMPTY channel (x 400..1240, y 132..204). Minimal:
> no extra ornaments. Then the same plate "running hot" for RAMPAGE mode with the tiny
> word RAMPAGE in the top-right corner. Then the luck segments at 76x48: an amber-gold
> slanted segment with a glow, its dark empty slot, and two white-hot sparking
> overcharge frames.

**C gauge** — attach `proposed_layout_mock.png`, `current_hud_art_BEING_REPLACED.png`, `i_tod_pm_pip_on.png`:
> Draw a slim vertical progress rail, 64x900, transparent outside: dark track, thin
> steel frame, a small flat gold CROWN glyph as the top cap (y 0..72) and a flat
> GROUND base plate as the bottom cap (y 828..900), a faint etched downward chevron
> near the top. The track between the caps is EMPTY. Then its twin with a jagged magenta
> spire-peak top cap and an upward chevron. Then the small pieces: a WHITE floor
> segment 40x24, a WHITE wider hub segment 56x24, a dark unreached segment 40x24, a
> magenta right-pointing "you are here" chevron 48x48, a magenta downed marker 48x48, a white
> horned-skull boss marker 48x48.

**D player** — attach `proposed_layout_mock.png`, `i_tod_class_medallion_necromancer.png`, `scoreboard_points_capsule.png`, `i_tod_pm_ico_damage.png`:
> Draw the pieces of a shell-less player readout: a thin chamfered health-bar frame
> 544x48 split into 15 equal cells with transparent insides; its WHITE fill strip
> 544x48 matching the inner area exactly; a half-height shield-bar frame 544x24 and its
> WHITE fill 544x24; the yellow Z points glyph alone at 128x128; WHITE 128x128 glyphs
> for downed, riot shield, and broken riot shield; and a thin octagon ring 256x256
> that frames the attached medallion, with a transparent inside.

**E gun / tiles / perks / toast** — attach `proposed_layout_mock.png`, `i_tod_pm_iconbtn.png`, `i_tod_pm_btn_focus.png`, and the KEPT icons that sit inside these frames: `i_tod_perk_jugg.png` (perk socket), `i_tod_hud_pap_2.png` (PaP tile), `i_tod_pu2_max_ammo.png` (toast well):
> Draw the gun plate 1056x288 (one low chamfered dark plate, magenta top edge, a faint
> gun-silhouette well on the left, everything else EMPTY), an ability tile 184x128 in
> three twins (plain steel frame, magenta READY glow, gold PaP frame) with EMPTY centres, a
> 128x128 perk socket with an EMPTY centre, and a 848x196 power-up toast plate with a
> gold top edge, an EMPTY round icon well on the left and an EMPTY name area.

**F glyphs** — attach `i_tod_pm_ico_damage.png` (the style), `current_hud_art_BEING_REPLACED.png` and `i_tod_hud_off_hook.png` (a current ability icon: what the glyph replaces, not its style):
> Draw 14 ability glyphs, 128x128, transparent, pure WHITE, flat and bold with a soft
> glow, in exactly the style of the attached white icon (list attached). Readable at 24x24.

**G gun silhouettes (optional)** — attach `i_tod_hud_gun_mp7.png`:
> Redraw each named gun as a flat light-steel side silhouette with one thin magenta accent
> line, 288x132, filling the frame like the attached file, same filename.

---

### 6. Delivery checklist

- [ ] 43 PNGs (+ any of G) + `_overview.png`, names exactly as above, lowercase.
- [ ] Every size exact; every width and height a multiple of 4.
- [ ] Transparent outside every piece; plates ~85% opaque.
- [ ] Every EMPTY area empty — no stray number, word, bar or icon.
- [ ] WHITE pieces are white only; the Z is yellow; luck is amber-gold; the crown gold; READY magenta.
- [ ] Twins line up pixel for pixel (status + rampage, tile + ready + pap, segment + off).
- [ ] `_overview.png` assembled from your files reads as MINIMAL at 1080p.

### 7. Do NOT

- Do not add a plate behind the player readout (it is shell-less on purpose).
- Do not bake numbers, names, floors, ammo or percentages anywhere.
- Do not redraw the class medallions, perk icons, power-up icons or PaP chevrons.
- Do not use cyan / Tron styling from the current HUD.
- Do not use any font other than the one in `typography/`.


<!-- PACK:END -->
