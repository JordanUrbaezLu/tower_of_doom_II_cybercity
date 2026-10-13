# 182 — SOUL PULSE: the Soul Bomb is renamed, re-set its baked text

<!-- art-pack
name: soul_pulse
refs:
  i_tod_card_soul_bomb_regular.png | THE CARD TO REDO, REGULAR rarity (shipped). Keep everything; change only the title and the description line.
  i_tod_card_soul_bomb_super.png | THE CARD TO REDO, SUPER rarity (shipped). Same change.
  i_tod_card_soul_bomb_ultimate.png | THE CARD TO REDO, ULTIMATE rarity (shipped). Same change.
  i_tod_pause_r59.png | THE PAUSE PLATE TO REDO (shipped). Change only the words.
  i_tod_card_summoning_power_regular.png | A sibling card from the same set, for reference only: how a two-word title sits in the banner.
preview: 186x279 300x44
-->

> **STATUS: SUPERSEDED 2026-10-04 (the Map 1 purge, R5): the art this asked for left the map. Do not send.**
> Was: **STATUS: REQUESTED 2026-09-26.** (The rarity faces can never be zoned again - docs/187; the Necromancer shows SOUL PULSE through i_tod_card2_art_soul_pulse.) The user renamed the Necromancer's lethal from
> SOUL BOMB to **SOUL PULSE** ("it should be like a soul pulse ... maybe we even
> change it to be soul pulse instead of bomb"), and the ability itself now reads as
> a pulse: a flat white ring sweeps out along the ground from the player
> (`make_soul_fx.py` RING_*), with no blast left at the centre. The game's text
> (card name, HUD tile, class select, card list) is renamed in script; FOUR images
> bake the old words and must be re-set: the three upgrade cards (title "SOUL BOMB",
> description "FASTER RECHARGE - WIDER BLAST", which is also stale - it charges on
> kills now) and pause plate r59. SAME FILENAMES, so a drop needs no wiring: install
> over the old files and run a FULL build. The ability glyph `i_tod_hud_off_soul_bomb`
> has no text and stays.

## Install (when the drop lands)

1. `.\tools\make_art_pack.ps1 -Inspect 'files (N).zip'` - 4 PNGs, sizes 768x1152 (cards)
   and the r59 plate at its shipped size, same colour type as the files they replace.
2. LOOK at each: title reads SOUL PULSE, description reads FEWER SOULS - WIDER PULSE,
   everything else pixel-identical in spirit to the shipped card.
3. Copy over `source_data/tod_ui_images/_images/` (same names), FULL build, prove with
   fresh content-hash `.iwi` for the four beside an untouched control.

<!-- PACK:BEGIN -->

# TOWER OF DOOM II — SOUL PULSE: re-set the text on 4 images

**4 PNG files.** An ability was renamed from **SOUL BOMB** to **SOUL PULSE**. Four
finished images carry the old name baked in. Re-make each one **exactly as it is**,
changing **only the words**.

## 1. What is in the zip

- `reference/i_tod_card_soul_bomb_regular.png`, `_super.png`, `_ultimate.png`: the three
  upgrade cards to redo. Keep the frame, rarity colours, banner, picture, rarity ribbon,
  pips, sparkles, lighting and layout exactly.
- `reference/i_tod_pause_r59.png`: the menu plate to redo. Keep the plate exactly.
- `reference/i_tod_card_summoning_power_regular.png`: a sibling card, reference only (how
  a two-word title sits in the banner). Do not deliver it.
- `typography/`: the game's typeface. **All text must be set in it.**
- `preview_onscreen_*/`: the references at their real on-screen sizes.

## 2. The changes

| File to deliver | Title / text | Description line |
|---|---|---|
| `i_tod_card_soul_bomb_regular.png` | **SOUL PULSE** | **FEWER SOULS - WIDER PULSE** |
| `i_tod_card_soul_bomb_super.png` | **SOUL PULSE** | **FEWER SOULS - WIDER PULSE** |
| `i_tod_card_soul_bomb_ultimate.png` | **SOUL PULSE** | **FEWER SOULS - WIDER PULSE** |
| `i_tod_pause_r59.png` | **SOUL PULSE** | (the plate has no description) |

Keep each card's rarity ribbon text exactly as on its reference (REGULAR +1, SUPER +2,
ULTIMATE +3).

**The picture (optional, small):** the card's picture is a ring of blue-grey souls
around a glowing skull. It already fits a pulse. If you touch it at all, make the ring
read as a flat ring spreading along the ground, not an explosion. Do not add a cloud or
glow ball at the centre. Leaving the picture unchanged is fine.

## 3. Hard rules

- Exact filenames above. Exact pixel size and format of each reference (same width,
  height, transparency).
- Text in the attached typeface only, same size, weight, outline and position as the
  old words. The title "SOUL PULSE" is one letter longer than "SOUL BOMB": keep it
  inside the banner with the same margins (shrink it very slightly if it must).
- Only these characters exist in the typeface: A-Z, 0-9, - ' . / +. No commas.
- Change nothing else: no new colours, no new effects, no re-lighting.

## 4. Prompt (paste with the four reference images attached)

"Re-create each attached image exactly, pixel for pixel in style and layout, changing
only its text. On the three upgrade cards: the gold title banner reads SOUL PULSE, and
the description panel reads FEWER SOULS - WIDER PULSE. On the thin menu plate: the text
reads SOUL PULSE. Use the attached typeface for all text, at the same size, outline and
position as the original words. Keep the frame, picture, ribbon, pips and every other
detail identical."

## 5. Delivery checklist

- [ ] 4 PNGs with the exact names in section 2.
- [ ] Each the same size and transparency as its reference.
- [ ] Titles read SOUL PULSE, spelled correctly, in the game typeface.
- [ ] Card descriptions read FEWER SOULS - WIDER PULSE.
- [ ] Rarity ribbons unchanged (REGULAR +1 / SUPER +2 / ULTIMATE +3).

## 6. Do NOT

- Do not redesign the cards or the plate.
- Do not change any word other than the ones listed.
- Do not add an explosion, cloud or glowing ball to the picture.
- Do not deliver the SUMMONING POWER reference.

<!-- PACK:END -->
