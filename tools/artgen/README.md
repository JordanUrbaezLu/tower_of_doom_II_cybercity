# artgen — self-serve assets (no human in the loop)

**Since 2026-10-04** (user: *"My typical flow regardless is sending to opus or fable anyways so
we could just update the process where we dont need me in the loop anymore"*), the session that
needs an asset also **makes** it. The art-request zip (`tools/make_art_pack.ps1`) is now the
FALLBACK, used only when the asset cannot be generated here. A game rip or licensed music needs
it. So does a judgement only the user can make by ear or eye, such as a voice pick.

## The loop

1. **Brief.** Write `docs/NN_<thing>_art_prompt.md` exactly as before. It stays the spec, the
   record and the fallback zip's source. Name the deliverables, sizes and the shipped files
   to match.
2. **Generator.** Write `tools/artgen/packs/<pack>.py`, importing `tools/artgen/artgen.py`:
   - no flag: write every deliverable to `art/generated/<pack>/`, plus
     `art/generated/<pack>/_review.png`, showing each image beside the shipped reference(s) it
     must match.
   - `--install`: copy the generated PNGs into `source_data/tod_ui_images/_images/`.
   - `--check`: regenerate in memory and fail on any byte that differs from the installed file.
     This becomes a build gate once the pack lands.
3. **Review.** A separate agent, never the author, opens `_review.png` and the deliverables at
   their real on-screen size. It checks them against the brief: legibility, style match,
   palette, baked text proofread against the code. Failing images go back to step 2.
4. **Land in one step.** Copy the images in, add the GDT block + zone `image,` line (new names
   only), and wire the Lua/GSC. Run the build's gate lines on the repo
   (`python tools/run_build_gates.py`) before a FULL build. Never leave a named-but-unzoned
   image (white square) or a zoned-but-unnamed one (dead weight); `tools/lint_tod_assets.js`
   enforces both.
5. **Build + log.** Run one FULL build for the batch (image changes always need FULL; geom_key
   reuses the bake). Flip the brief's STATUS to SHIPPED, with the build. Then the user plays.
6. **Refresh the Art Atlas** (the user's browsable gallery of every in-game image). Run
   `python tools/art_gallery/build_gallery.py`, then republish it to the same link
   (`tools/art_gallery/README.md`). Also do this when generated art first lands in
   `art/generated/`, so the user can see work in production.

## THE ONE LIBRARY (user 2026-10-05: "Whole entire asset library should look like one library")

Every in-game image belongs to one of these families. A new image joins a family and is drawn by that family's
generator (or a pack that imports its helpers); it never invents a new look. Open the family's newest member
before drawing.

| Family | Look | Owner (generator, `--check` gated) |
|---|---|---|
| Chrome: panels, plates, badges, banners, prompt cards, pause / scoreboard, Black Market frame | chamfered CHARCOAL GLASS, grey scratched steel hairline, ONE lit line in the theme accent (Fallen red) on an edge or an L, red splatter in a corner; never a bright flat panel, never hazard stripes | `synthwave.py` + `r3_synthwave_system.py`, `r4_synthwave_hud.py`, `bm_chrome.py` (the Black Market reel, re-lit from its parked delivery) |
| Glyph icons: perks, power-ups, prompts, abilities, pause rows, class medallions | WHITE-HOT ink with ONE hue accent on the part that matters, inside a black-glass well or shield with the hue tube; ink kept inside the well (perks / power-ups inset, never touching the tube) | `r4_synthwave_hud.py` (`neon_glyph`), `w3b_ability_colour.py`, `w3c_class_pack.py` |
| Weapon bay icons `i_tod_hud_gun_*` | three tones only (navy outline, slate shade, pale light), traced from the weapon's real model, pointing right | `r1_gun_icons.py`, `gun_bay_icons.py` |
| Card illustrations `i_tod_card2_art_*` | flat cartoon on the card2 navy starfield, thick navy outline, 2-3 tones per part; a WEAPON is rendered from its real model (`r2` / `r5` render + stylize), never drawn from memory | `r2_card_subjects.py`, `r5_tier_subjects.py` |
| Portraits: the Dealer, the companions | flat vector, strong silhouette, two or three tones per part, neon accents, the shared backdrop | `dealer_house/make_spin_art.py`, `r1_comp_portraits.py` |
| Words baked into art | OUR typeface only (`artgen.typeset`); the retired face (S drawn as 5) must never appear | every pack |

THE UI THEME IS ONE SWITCH (docs/218_red_return.md, 2026-10-05): `tools/artgen/synthwave.py` `THEME = 'fallen'` (the red Fallen UI,
docs/171 Theme B + docs/180-183; user: "id rather the red theme please") or `'synthwave'` (docs/184). A pack names
ROLES from `synthwave.PAL` (`magenta` = frame light / ready / the accent word, `cyan` = focus / rules / lit pips,
`accent2` = a second lit colour on a framed piece, `idle_edge`, `dead_red`, the darks ...), never a theme's hex: a ROLE
follows the theme, a literal `#RRGGBB` (a class / rarity / perk hue) or an `id_*` role (a power-up's hue) never moves.
The code tints follow the same switch and are gated (r3 CODE_TINTS: the pause menu, scoreboard and THE PULL's pips /
stamp word; r4 ROUND2_TINT; pk09 GSC_TINTS; w2g CP_TINTS: the companion plate's state tints; bm_chrome LUA_TINTS: the
Black Market reel). A pack that has nothing to generate in one theme parks the delivered art and returns its exact
bytes there (r10's PULL stamp, bm_chrome), so reverting the theme restores a delivery to the byte.

Truth rules: a picture of a weapon, companion or enemy shows the one the game hands out (read `_tod_classes.gsc`
`register_gun` and the weapon GDT's `gunModel`, never the asset's name). Colour carries meaning: class hues are
`tod_class_select.lua` `CLASSES[].accent`; rarity hues are white / blue / violet / gold (+ red CURSED); red is for
enemies and danger, white for allies (health bars).

## Rules the generators follow

- **Our typeface for every letter and number.** Use `artgen.typeset()` (the glyph-sheet cells
  TodGlyphRow draws in game) or `artgen.ttf()`. The glyph set is A–Z, 0–9, `- ' . $ + /`.
  `+` and `/` live only in the digit set; `typeset` routes them.
- **Match the shipped neighbours.** Open the reference, measure its size and sample its palette
  (`artgen.palette()`). Copy its outline weight and shading steps, in its family's look (THE ONE
  LIBRARY, above).
- **Sizes are multiples of 4** (`save_png` refuses others; the converter silently writes no
  .iwi).
- **Deterministic output.** No randomness without a fixed seed and no timestamps in the files,
  so `--check` can gate the bytes.
- **Never hand-edit a generated PNG.** Change the generator and re-run it.

## Other asset types

| Asset | Route |
|---|---|
| 2D UI art (icons, cards, plates, badges, banners) | `artgen` (SVG via resvg_py, glyph-sheet text) |
| Re-baked text on existing art | `artgen.typeset` over the existing image, background sampled |
| Sound effects | ElevenLabs sound generation (`ELEVENLABS_API_KEY`), measured and levelled like `tools/ability_fx/make_sounds.py` |
| Voice lines | ElevenLabs voice (`tools/black_market_vo/` pattern). The user approves voices by ear. |
| Effects (.efx) | compose from existing BO3 emitters (`tools/haven/make_fx.py` pattern); never zone a `gfx_debug_missing_fx` stub |
| Models / textures | Blender MCP studio, its own port, plus the native export/installer pattern |
| Game rips, licensed music | **user**: build the zip with `tools/make_art_pack.ps1` |
