<!-- art-pack
name: elite_hpbar
refs:
  source_data/tod_hud_bars/_images/i_tod_hpbar_e_10.png | the CURRENT placeholder ELITE bar at full health, rest frame (336x72 canvas). Match the canvas size, the bar's position inside it and the proportions. Its WHITE colour is a placeholder: the new set is RED.
  source_data/tod_hud_bars/_images/i_tod_hpbar_e_06.png | ELITE rest frame at 60 %. The fill grows from the LEFT; the frame never moves.
  source_data/tod_hud_bars/_images/i_tod_hpbar_e_06_h2.png | ELITE PEAK hit frame at 60 %: only the fill's right edge swells past the frame and glows. Everything else is identical to the rest frame.
  source_data/tod_hud_bars/_images/i_tod_hpbar_e_06_h1.png | ELITE SMALL hit frame at 60 %: the same edge, smaller.
  source_data/tod_hud_bars/_images/i_tod_hpbar_e_00.png | ELITE empty (track only). Has no hit frames.
  source_data/tod_hud_bars/_images/i_tod_hpbar_b_10.png | the BOSS bar placeholder, full (544x80 canvas).
  source_data/tod_hud_bars/_images/i_tod_hpbar_b_06_h2.png | BOSS peak hit frame at 60 %.
  docs/174_elite_hpbar_art/preview_sheet.png | a hit sequence at native size: rest, peak, small, rest.
  docs/174_elite_hpbar_art/preview_screen.png | both sets at their real 1080p on-screen size, every fill step plus one hit sequence each. Judge legibility HERE.
preview: 252x54 408x60
-->

# 175 — Elite health bar art, the user's own RED set

**Status: SUPERSEDED 2026-10-01** — the drop never came; on the user's "change the elite bars to red" the generator (`tools/gen_hpbar_art.js`) now draws the red set itself and a WHITE set for the Necromancer's helpers (docs/174 "Third pass"). If a hand-made red set ever arrives, install it over `i_tod_hpbar_e_*` / `_b_*` only — `test_elite_hp.js` checks the colour — and stop re-running the generator for those two sets. Original request: **REQUESTED 2026-09-25 by the user** ("I'll get those HP bar assets soon. I'm
making them red instead"). Rewritten the same evening for the second build: the bar grew
(user: "too small ... both height and width") and the hit pulse moved from the whole bar
to the fill's right EDGE, which is baked into two extra frames per fill step. So the
delivery is **62 files**, not 22.

Install (no wiring, same names): `.\tools\make_art_pack.ps1 -Inspect 'files (N).zip'`,
look at every image, copy the 62 PNGs over `source_data/tod_hud_bars/_images/`, run
`node tools/test_elite_hp.js` (it checks every name and size), FULL build. **Do NOT re-run
`tools/gen_hpbar_art.js` after installing a drop** — it rewrites these PNGs with the white
placeholders. If the drop's canvas differs, change the generator's spec and the script's
`TOD_HPBAR_*_W/H` together (the gate checks draw size = PNG size / 4).

<!-- PACK:BEGIN -->
# Elite health bars — RED

Small health bars that float above the heads of the game's elite enemies and drain from
right to left as they take damage. The game draws each bar at a fixed size and swaps
between pictures: one picture per 10 % of health, plus two "hit" pictures per step that
make the **right edge of the remaining health** pulse like a hit marker when the enemy is
shot. The files in `reference/` are WHITE placeholders showing the exact layout; the new
set is **RED**.

## Deliverables — 62 PNG files, RGBA, exact names, exact sizes

| Set | Canvas (px) | Bar body inside it | On screen at 1080p | Used on |
|---|---|---|---|---|
| ELITE `i_tod_hpbar_e_…` | **336 x 72** | 304 x 40, centred (16 px transparent margin on every side) | 252 x 54 | every elite |
| BOSS `i_tod_hpbar_b_…` | **544 x 80** | 512 x 48, centred (16 px margin) | 408 x 60 | the two biggest bosses |

Per set, 31 files:

- **Rest frames** `_00` … `_10`: the bar with its fill at 0 %, 10 %, … 100 %, anchored at
  the LEFT of the track. `_00` is the empty track.
- **Hit frames** `_01_h1` … `_10_h1` (small) and `_01_h2` … `_10_h2` (peak): the SAME
  picture as that step's rest frame, plus a pulse on the fill's right edge. There are no
  hit frames for `_00`.

Full list for one set (replace `e` with `b` for the boss set):
`i_tod_hpbar_e_00.png`, then for NN = 01 … 10: `i_tod_hpbar_e_NN.png`,
`i_tod_hpbar_e_NN_h1.png`, `i_tod_hpbar_e_NN_h2.png`.

## The hit pulse

- It sits ONLY at the right end of the fill, where the remaining health ends. Nothing
  else in the picture changes: frame, track and the rest of the fill must be
  pixel-identical to that step's rest frame, or the whole bar will flicker on every hit.
- `_h2` (peak): a bright notch at the fill's edge that swells **past the frame top and
  bottom into the transparent margin** (about 12 px beyond the track each way on the
  ELITE set), with a soft glow, and the last stretch of fill heated brighter.
- `_h1` (small): the same notch at roughly half the swell and glow.
- The game plays peak, then small, then back to rest, in about 0.3 s. Do not bake any
  other animation.
- The glow may spill into the margin, but must stay inside the canvas.

## Look and hard rules

- **RED fill.** Your call on the exact red: it must read clearly as red at 252 x 54 px
  against both a near-black night sky and bright neon. The pulse can run hotter (toward
  orange-white or pink-white) so it pops against the red.
- Dark, slightly translucent track (near-black, about 85 % opaque) so the fill reads.
- A thin frame with a 1–2 px dark outer gap so it separates from bright backgrounds.
- The margin around the bar body is TRANSPARENT on every rest frame.
- The game downscales these about 4:3 with bilinear filtering: **no line thinner than
  3 px in the source**, no fine noise, no tiny detail.
- The BOSS set may be more ornate (corner studs, notches at thirds); the ELITE set is
  plainer (notches at quarters or none). Both must clearly be the same family.
- No text, numbers or icons inside the bar.

## Prompt

Attach `reference/i_tod_hpbar_e_10.png`, `reference/i_tod_hpbar_e_06.png`,
`reference/i_tod_hpbar_e_06_h2.png`, `reference/i_tod_hpbar_e_06_h1.png`,
`reference/i_tod_hpbar_e_00.png` and `reference/preview_sheet.png`:

> A futuristic enemy health bar on a 336x72 transparent canvas, the bar body 304x40
> centred with a 16 px empty margin. Thin frame with a dark outer gap, near-black
> smoked-glass track, a RED fill lit from the top, drawn from the left. Match the
> reference layout exactly; only the colour changes from white to red. Deliver the fill at
> 0, 10, … 100 %. For every step from 10 % to 100 %, also deliver two hit frames that are
> identical except for a bright, glowing notch at the fill's right edge that swells past
> the frame into the margin: a large one (peak) and a half-size one (small).

Then the same at 544x80 (bar body 512x48) for the boss set, slightly more ornate. Attach
`reference/i_tod_hpbar_b_10.png` and `reference/i_tod_hpbar_b_06_h2.png`. Check both sets
against `reference/preview_screen.png`, which shows them at their real on-screen size.

## Delivery checklist

- [ ] 62 files, exact names, exact canvas sizes, RGBA PNG
- [ ] in each set, the rest frames differ only in the fill length
- [ ] each hit frame differs from its rest frame ONLY around the fill's right edge
- [ ] margins transparent on rest frames; pulse glow stays inside the canvas
- [ ] reads RED at 252x54 / 408x60 px
- [ ] no line under 3 px, no text

## Do NOT

- change the canvas sizes, the bar body size or its position
- rename files, or drop the `_h1` / `_h2` frames
- put the pulse anywhere but the fill's right edge
- add a number, skull, icon or label
<!-- PACK:END -->
