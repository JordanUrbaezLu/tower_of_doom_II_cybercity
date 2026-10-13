# 183b — PROMPT-CARD ICONS: the Black Market and the Battle Arena (PK07)

<!-- art-pack
name: prompt_icons_black_market_arena
refs:
  i_tod_prompt_icon_rampage.png | THE STYLE. A shipped prompt icon: bold flat white glyph, one red accent, soft white glow, transparent background.
  i_tod_prompt_icon_alarm.png | THE STYLE. A shipped prompt icon with a larger red accent area.
  i_tod_prompt_icon_crate.png | THE STYLE. A shipped prompt icon: an object built from flat white bars with transparent cut-outs.
  i_tod_prompt_icon_teleporter.png | THE FLOOR GRAMMAR. An object standing on a perspective ellipse.
  i_tod_prompt_icon_generic.png | BEING REPLACED for these two objects. The fallback hand they draw today.
  i_tod_spin_dealer_idle.png | THE LIKENESS. The Black Market Dealer: black hood, angular mask, red X eyes, stitched red grin.
  i_tod_spin_ico_cursed.png | THE LIKENESS. The Dealer's mask as a small icon.
  i_tod_h2_arena_badge.png | THE SUBJECT. The Battle Arena's HUD badge (its red edge light).
preview: 66x66
-->

> **STATUS: GENERATED + STAGED 2026-10-04 (PK07), NOT LANDED, NOT BUILT, UNPLAYED.** The session
> that found the gap made the art (tools/artgen/README.md). Generator
> `tools/artgen/packs/pk07_prompt_icons.py`; output `art/generated/PK07-prompt-icons-new/`
> (review sheet `_review.png`); the landing kit (two PNGs, two GDT blocks, two zone lines, two
> ICONS rows) is staged under `tmp/asset_prod/PK07-prompt-icons-new/` with its `LAND.md`.
> The CLASS TERMINAL icon is drawn only with `--terminal` and is NOT staged: `TOD_TESTER_KIT` is 0.

## The design (repo-facing)

**The gap.** Every interaction prompt draws one 256x256 icon in the prompt card's well, picked by
`CoD.TodPromptCard.IconFor()`: a first-match search of the lowercased hint line against the
`ICONS` table in `TodPromptCard.lua`, falling back to `i_tod_prompt_icon_generic` (a pointing
hand). The Black Market has three hints (the spin, `_tod_shop.gsc:345`; THE DEALER'S GIFT,
`:347`, the first Black Market use of every run; the House's last roll, `_tod_house.gsc:105`)
and the Battle Arena chamber four (`_tod_arena.gsc:204-207`). None had a row, so all drew the
hand, except the unpowered arena, which the `power required` row already claims.

**The fix.** Two generated icons and two rows:

| Row (phrase) | Icon | Where in the table |
|---|---|---|
| `black market` | `i_tod_prompt_icon_black_market` | after `the alarm`; no other row is contained in it |
| `battle arena` | `i_tod_prompt_icon_arena` | BELOW `power required` (first match wins), so the unpowered chamber keeps the power icon |

**The style is measured, not eyeballed.** Over the shipped docs/183 set: solid ink pure white,
accent (242, 32, 58), cut-outs transparent, one Gaussian glow of the solid coverage (sigma 9 px,
strength 0.65; least-squares fit over eight shipped icons, RMSE about 2.4/255 in alpha), white
parts glow white and red parts glow red, the solid box spanning about 72-87% of the canvas.
The accent stays red: no synthwave prompt-icon set (docs/184d) has landed.

**The two glyphs.**
- **The Dealer** (docs/dealer_identity.md): a rounded deep hood (never a peak: a white pointed hood
  is the one silhouette this must never read as) falling to the shoulders; the long angular
  faceted mask inside it with an even dark gap; red X eyes slanted toward the nose, one stroke a
  touch weaker as on the shop model; an uneven stitched red grin. The mask is whole (no
  brow-to-chin crack: that is the boss's cracked state, docs/199). The mask is WHITE, not
  charcoal, because every icon in the set is a white glyph; the cut-outs carry the shape.
- **The Battle Arena**: two crossed blades standing in the arena ring. The ring is a perspective
  ellipse (the teleporter / extract floor grammar) and the red accent: the arena pit's lit edge.
  The blades knock dark gaps out of the ring's far side only, so they stand inside it. A full red
  circle round crossed blades was tried and dropped: at 66 px it reads as "no weapons".

**Readability.** Each icon is seen at about 66 px (1080p) and 44 px (720p). The review sheet shows
both sizes beside the shipped set, plus the four live card states at chassis scale and true size.

**The gate.** `python tools/artgen/packs/pk07_prompt_icons.py --check` fails on any byte that
differs from the generator, a missing GDT block / zone line / ICONS row, a GDT block that is not
`compressed high color`, the arena row above `power required`, or a row whose phrase no live hint
carries any more (a renamed hint would silently fall back to the hand). Six negative controls
were run against it on 2026-10-04 (arena row moved above power, zone line removed, a stealing
row inserted above, one pixel changed, compression changed, the arena hint renamed); all six fail.

<!-- PACK:BEGIN -->
# Two prompt-card icons: the Black Market Dealer and the Battle Arena

You are drawing two small icons for a video game's interaction prompt. When a player walks up to
something they can use, a card pops up with an icon on the left. Every object in the game has its
own icon. Two objects do not yet, and today they show a plain pointing hand.

## Deliverables

| File | Size | Subject |
|---|---|---|
| `i_tod_prompt_icon_black_market.png` | 256 x 256, RGBA | The Black Market's dealer: a deep rounded hood around a long angular mask with red X eyes and an uneven stitched red grin |
| `i_tod_prompt_icon_arena.png` | 256 x 256, RGBA | The Battle Arena: two crossed swords standing inside a red ring seen in perspective (a flat ellipse) |

## Hard rules

- Match the reference icons exactly in style: a bold, flat, pure WHITE glyph, ONE red accent
  colour (RGB 242, 32, 58), a soft white outer glow (red parts glow red), transparent background.
- No plate, circle or frame behind the icon. Holes in the shape are transparent, not grey.
- The glyph fills about 70-85% of the square, centred.
- No text, no letters, no numbers.
- It must read at 66 x 66 pixels and still read at 44 x 44. Check both before delivering.

## Prompts

**Black Market** (attach `reference/i_tod_prompt_icon_rampage.png`,
`reference/i_tod_spin_dealer_idle.png`, `reference/i_tod_spin_ico_cursed.png`):
> A 256x256 transparent PNG icon in the same flat style as the attached white skull icon: a bold
> white glyph of a hooded figure's head and shoulders. A deep ROUNDED hood (not pointed) frames a
> long angular faceted white mask, with an even dark gap between hood and mask. The mask has two
> red X eyes and an uneven, lopsided red stitched grin with short stitches crossing it. Only red
> and white. Soft white outer glow, red parts glow red. Transparent background, no plate.

**Battle Arena** (attach `reference/i_tod_prompt_icon_teleporter.png`,
`reference/i_tod_prompt_icon_crate.png`, `reference/i_tod_h2_arena_badge.png`):
> A 256x256 transparent PNG icon in the same flat style as the attached white icons: two white
> straight swords crossed in an X, hilts down, standing inside a thick red ring drawn as a flat
> perspective ellipse at the bottom of the icon. The swords cut small dark gaps where they pass
> over the ring's far side. Only red and white. Soft white outer glow, red parts glow red.
> Transparent background, no plate.

## Delivery checklist

- [ ] Two PNGs, exact names, exactly 256 x 256, RGBA, transparent background.
- [ ] White glyph with one red accent; no other colours.
- [ ] Readable at 66 px and at 44 px on a dark background.

## Do NOT

- Do not draw a pointed hood, a peaked cowl or anything that reads as a costume hood.
- Do not draw a full red circle around the swords (it reads as a "no weapons" sign).
- Do not add a backing plate, a frame or any text.
<!-- PACK:END -->
