<!-- art-pack
name: typeface_options
typography: off
refs:
  source_data/tod_ui_images/_sheets/i_tod_hud_letters.png | THE CURRENT ALPHABET SHEET. The face all three options start from. 15 x 2 grid of 80 x 112 cells. Cell 28 (the gold coin) is our own points symbol, not part of the task.
  source_data/tod_ui_images/_sheets/i_tod_hud_digits.png | THE CURRENT NUMERAL SHEET. 13 x 1 row of 128 x 160 cells. Same face as the letters.
preview: 546x53 386x72
-->

# 172 — Typeface: THREE OPTIONS close to the Tower 1 face: art request

**THE LEGIBILITY REVISION (2026-09-29, session d2; user: "our typography is a little bit hard to read
... the letters and symbols are a little bit too thick ... I'm not looking for major, major changes. I
just want it to be a little bit easier to read ... maybe more round ... I don't want ... to go back to
the old one ... our asset request zip also gets the new typography").** Measured on the shipped face:
the capital I at mid-height was 5 px outline + 15 px face + 5 px extrusion + 6 px outline, so the dark
outline and the blue-grey extrusion doubled every stroke, and the extrusion fell INSIDE every counter
(O, B, 8, A, R) and shrank the holes that make a letter readable at 12-20 px; and the S was the digit 5's
shape (square top-left corner, straight stem), so "BLASTS" read "BLA5T5". The revision keeps every
letterform and every cell / baseline / ink box, and changes only:
- the stroke: 15 -> ~12.8 px letters, 23 -> ~19 px numerals (each glyph eroded, then scaled back onto its
  old ink box, so sizes and spacing are unchanged);
- the extrusion: 5 -> 3 px letters, 8 -> 5 px numerals; the outline 5 -> 4.5 px;
- the corners: a 3 px round on the outer corners and 1.5 px on the inner ones;
- THE S, redrawn as one stroke in the old S's box with its four bends rounded about one stroke wide and
  short hooked ends; the 5 keeps its square corner (only 1.5 px of round), so the two never read alike;
- the gold points coin is untouched.
THE MENUS' FONT (`fonts/tod_tower1.ttf`, built from the sheets by `tools/build_tod_ttf.py`) followed with
two fixes of its own: the % is two RINGS around the slash (the square blocks read "85%" as "857."; six
designs were set at 13-32 px and only rings read as a percent at every size), and HORIZONTAL_FIT
0.94 -> 0.91, because the thinner outline left a wider steel face and every menu line had grown 3.3%
(0.91 puts the real menu text back on its old width; `tools/ui_mockup/render_menus.py --check`).
The new sheets ARE the masters now (`source_data/tod_ui_images/_sheets/`); the glyph images, metrics, the
menus' font (`fonts/tod_tower1.ttf`) and the specimen are built from them, and
`art/typeface/typeface.json` pins them (`python tools/typeface/typeface.py --check`, a build gate). The
old face (and the drafts before it) moved to `archive/typeface_retired/`, which nothing live reads, with
the one-time script that drew the revision from it. Every art pack carries the new face automatically.

**Status: SHIPPED 2026-09-25 — the user chose OPTION A (Tower 1 Refined, rev 2). Sheets in `_sheets/` (points coin composited back into cell 28, 1 px lower for the new baseline 104), sliced; originals + all three options' record in `art/typeface/`. The art-pack tool now ships this face in every pack (`typography/`).**

User, 2026-09-25: *"we need a new typography set ... 3 new options. Very similar to old
one with slight differences to each. One of them should be a poppins style mix with our
current tower 1 typography."*

Companion to docs/171 (the class-art theme audition, sent the same day). The typeface is
the map's own bitmap face: two sheets sliced by `tools/slice_hud_sheets.js`, metrics
derived into `TodGlyphMetrics.lua`, drawn by every prompt card, the weapon name, the
ammo counter, the class HUD. Originally commissioned in docs/95 (Prompts E/F); the rules
below are that brief's rules, kept, because the slicer and renderer depend on them.

## What must stay identical, and why (repo-facing)

- **Canvases and grids** (1664x160 / 13x1 of 128x160; 1200x224 / 15x2 of 80x112) and
  **cell order** — the slicer is arithmetic.
- **One baseline and one cap height per sheet** — the slicer's GATE 3; a wobbling
  baseline makes the ammo counter step.
- **Steel-white face** — clip digits are runtime-tinted RED and pulsed at low ammo; a
  baked hue goes muddy.
- **Proportional widths** — advances are MEASURED from the art.
- **Cell 28** of the letters sheet is our composited points coin (was the ampersand,
  v19.2). The generator leaves it EMPTY; we composite the coin back in before slicing.

## After the drop (repo-facing, not in the pack)

`.\tools\make_art_pack.ps1 -Inspect "files (N).zip"`, then for each option
`node tools/slice_hud_sheets.js --check --src <option folder>` (canvas, bleed, baseline,
cap height). Render the test strings with each option's sheets for the user side by side.
The chosen option: composite the coin into cell 28, copy both sheets to `_sheets/`,
slice with `--src source_data/tod_ui_images/_sheets`, FULL build. Same filenames = no wiring.

<!-- PACK:BEGIN -->

# TOWER OF DOOM II — the game's custom TYPEFACE: THREE OPTIONS

**6 PNG files: two sheets (letters + numerals), drawn three slightly different ways.**

This zombies map draws all its HUD text with its own hand-made bitmap typeface: weapon
names, the ammo counter, points, prompts. The current face is in `reference/`: a blocky,
bold, squarish "machine readout" face with a steel-white fill, a dark outline and a hard
grey-blue shadow offset down-right.

We like it, and we want **three new options that stay CLOSE to it** — each a fresh take
with its own small personality, not a different font. Someone who knows the current face
should recognise every option as its sibling.

---

## 1. Deliverables

Three folders, `option_a/`, `option_b/`, `option_c/`. Inside each, exactly:

| File | Canvas | Grid | Shown on screen at |
|---|---|---|---|
| `i_tod_hud_digits.png` | **1664 x 160** | 13 x 1 cells of 128 x 160 | up to 42 x 60 per glyph |
| `i_tod_hud_letters.png` | **1200 x 224** | 15 x 2 cells of 80 x 112 | up to 27 x 36 per glyph, as small as 14 x 18 |

Plus, per option, `option_X/_test.png` (any size, dark navy background): the test lines
from section 6 set with that option's own glyphs. It is only for choosing.

Plus one short `OPTIONS.md`: each option's name and 2-3 sentences on what changed from
the current face.

PNG, RGBA, fully transparent background. Same filenames in every folder on purpose.

---

## 2. The three options

**All three keep the current face's structure:** uppercase only, upright, bold, a
steel-white face, a dark outline, a hard shadow offset down-right. The differences are in
the LETTERFORMS.

### Option A — TOWER 1 REFINED
The current face, cleaned up and made a touch more elegant. Same squarish construction
and weight, but crisper, more consistent corner cuts, slightly more generous counters
(the holes in A, B, O, 8...), better-balanced widths, tidier diagonals in K, V, W, X, Y,
and a more confident S and G. The "same font, drawn by a better hand" option.

### Option B — POPPINS MIX
**A blend of the geometric sans-serif Poppins and the current Tower 1 face.** Take from
Poppins: near-perfect circular bowls in O, C, G, Q, D and the round parts of B, P, R, S,
6, 8, 9, 0; clean geometric construction; even, modern proportions; round-ended feel on
curves. Keep from Tower 1: the heavy weight, the steel-white face, the dark outline, the
hard down-right shadow offset, the flat-topped straight strokes on E, F, H, I, L, T, and
the chunky game-HUD attitude. The result should read as "Poppins Black, built for a
sci-fi game HUD" — rounder and friendlier than Tower 1, but unmistakably in the same
family. Do not simply trace Poppins; it is an influence, not a copy.

### Option C — TOWER 1 SHARP
The current face pushed slightly more technical: bigger 45-degree chamfers instead of
small corner cuts, a few angled terminals (on C, G, J, S, 2, 3, 5), a very slightly
narrower build, and small notches or cuts that hint at machined metal and crystal
facets. Still blocky, still bold, still clearly Tower 1 — just harder-edged, for a darker,
more serious city.

---

## 3. The cells (identical for all three options)

**Numerals — `i_tod_hud_digits.png`**, 13 cells left to right:

    0   1   2   3   4   5   6   7   8   9   /   +   -

**Letters — `i_tod_hud_letters.png`**, 30 cells, reading order:

    row 1:  A B C D E F G H I J K L M N O
    row 2:  P Q R S T U V W X Y Z - '  [EMPTY]  .

**Cell 28 (row 2, the 14th cell) must be LEFT EMPTY** — fully transparent. The game
puts its own points symbol there. Everything else filled, in exactly this order.

---

## 4. Hard rules (these make the font work in the game — do not break any)

**Sheet format**
- Canvas EXACTLY the stated size. The sheet is cut by arithmetic: cell n starts at
  n x cell width. A sheet 2 px too wide cuts wrong on every glyph.
- No gutters, no margins between cells. Nothing may touch or cross a cell edge — keep
  each glyph inside about 85-90% of its cell.
- NO grid lines, frames, labels, backgrounds, guide marks or baseline rules drawn.

**Type**
- **One baseline and one height per sheet, matching the current sheets.** Measured on
  the reference art, each glyph's TOTAL ink (face + outline + shadow) is:
  numerals about **137 px tall, bottom edge at y = 152** of the 160 px cell;
  letters about **89 px tall, bottom edge at y = 103** of each 112 px row.
  Hit those in all three options. If one glyph sits 4 px higher than another, the ammo
  counter visibly wobbles as the number changes.
- **One stroke weight across every glyph**: about 26 px on the numerals, about 16 px on
  the letters (the same proportion). Letters and numerals are used together in one
  line ("AK-47", "R-99", "SPAS-12"), so they must be one family.
- **Tones:** face steel-white **#E8EEF6**; outline **#0A1020** (~8 px numerals, ~5 px
  letters); the shadow offset is ONE darker cool grey-blue, hard-edged, down and to the
  right (~8 px numerals, ~5 px letters), same direction everywhere. No gradients, no
  glow, no texture. The game tints these glyphs at runtime (the ammo counter turns red
  when low), so the face must stay near-white and neutral.
- **Uppercase only.** No lowercase. Upright only, no italics.
- **Proportional, not monospace:** draw each glyph at its natural width, centred in its
  cell. The game measures each glyph's width from your art. (Rough guide: 1 and I
  narrow; M and W wide; most letters 42-56 px; most numerals 85-95 px.)
- **Counters** (enclosed holes) at least 20 px across on numerals, 12 px on letters.
- **Marks:** `/` narrow and steep, full cap height. `+` a plain cross sitting HIGH, on
  the numerals' upper half (used as "+3"). The numeral `-` is a wide, substantial bar at
  mid height (it replaces a number, so it must weigh like one). The letter `-` is a
  shorter hyphen for words. `'` a short mark at cap height. `.` a small square on the
  baseline.

**Legibility pairs** — must be clearly different at 27 x 36 px: 0 / O / Q (Q with a bold
tail), 1 / I / 7 (I with top and bottom bars, 7 with a crossbar or clear diagonal),
6 / 8 / 9 / 0, S / 5, C / G, E / F, P / R, U / V, M / N, B / 8.

---

## 5. What makes the three different

Only the letterforms: curve vs. corner construction, chamfer size, terminals, widths,
counter shapes. **Not** the colours, outline, shadow direction, weight, cap height or
baseline — those are the same in all three, so any option drops straight into the game.

---

## 6. Test before delivering (and put it in `_test.png`)

Cut each sheet into its cells, shrink numerals to 42 x 60 and letters to 27 x 36, and set
these on a dark navy background:

    1234567890
    32 / 240
    - / -
    +3
    AK-47
    R-99 SPAS-12 M1927
    STORMBREAKER EX
    RASPUTIN'S RETRIBUTION
    TOWER OF DOOM II
    FALLEN CYBERCITY

Every line dead level, every glyph identifiable. Then shrink the longest line to half that
size — the game does exactly that for long weapon names — and check it still reads.

---

## 7. Delivery checklist

- [ ] `option_a`, `option_b`, `option_c`, each with `i_tod_hud_digits.png` (1664 x 160)
      and `i_tod_hud_letters.png` (1200 x 224), RGBA, transparent
- [ ] Every cell in the listed order; letters cell 28 EMPTY
- [ ] No grid lines, labels or backgrounds on the sheets
- [ ] One baseline, one cap height, one stroke weight per sheet
- [ ] Face #E8EEF6, outline #0A1020, one hard down-right shadow tone
- [ ] Option B visibly rounder (Poppins-style bowls) yet still a sibling of the current face
- [ ] `_test.png` per option and `OPTIONS.md`

## 8. Do NOT

- Do not change the canvas size, grid, cell order or cell 28.
- Do not add lowercase, italics, gradients, glow or texture.
- Do not make any option look like a different font family — all three are variations.
- Do not make the face monospace.
- Do not deliver glyphs as separate files; the sheet is the format.

<!-- PACK:END -->
