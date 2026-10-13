# RETIRED TYPEFACES - do not use

Nothing in the game, the build, the HUD, the menus or the art packs reads this folder, and
`python tools/typeface/typeface.py --check` (a build gate) fails if a live file ever names it.
It is kept only as history.

**The live typeface** (the 2026-09-29 legibility revision, docs/172 section 7):
- masters: `source_data/tod_ui_images/_sheets/i_tod_hud_letters.png` and `i_tod_hud_digits.png`
- built from them: the `i_tod_hud_l*` / `i_tod_hud_d*` glyph images (`tools/slice_hud_sheets.js`),
  `TodGlyphMetrics.lua`, `fonts/tod_tower1.ttf` (`tools/build_tod_ttf.py`) and
  `art/typeface/specimen.png` (`tools/typeface/typeface.py --specimen`), pinned by
  `art/typeface/typeface.json`.

| folder | what it was |
|---|---|
| `2026-09-29_option_a_rev2/` | the face shipped 2026-09-25 .. 2026-09-29 (docs/172 option A rev 2): its two sheets, the font built from them, the specimen and proofs, and `retypeset.py`, the one-time script that drew the 2026-09-29 revision FROM these sheets (thinner stroke, lighter extrusion, rounder corners, a redrawn S). |
| `option_a_refined/` | the docs/172 option A drop as delivered (before it was installed). |
| `tower1_original/` | Tower of Doom 1's face, the one option A redrew. |

User, 2026-09-29: "I don't want you know, in our future to go back to the old one. Maybe we can
delete the old one, and only keep the new one, or at least just move it out so that nothing
references those at all."
