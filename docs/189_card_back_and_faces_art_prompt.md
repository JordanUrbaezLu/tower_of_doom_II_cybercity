<!-- art-pack
name: card_back_and_faces
refs:
  docs/189_ref/face_remove_these_three.png | THE EDIT, in one picture: a current card with the three things to REMOVE boxed in red (the rarity word band, the round rarity gem, the row of level dots). Every face in this pack is exactly this edit. Attach to Prompt B.
  i_tod_card_luck_regular.png | a current card face, untouched: the frame, title plate, art window and description box all STAY exactly as drawn. Attach to Prompt A (style) and Prompt B.
  i_tod_card_grapple_regular.png | a second current face, to show the family look is shared. Attach to Prompt A.
  i_tod_card_riot_shield_regular.png | a third current face. Attach to Prompt A.
  i_tod_card_dmg_reduction_regular.png | face to edit (DMG REDUCTION)
  i_tod_card_bounty_regular.png | face to edit (BOUNTY)
  i_tod_card_adrenaline_regular.png | face to edit (ADRENALINE)
  i_tod_card_summoning_power_regular.png | face to edit (SUMMONING POWER)
  i_tod_card_retriever_regular.png | face to edit (HELL'S RETRIEVER)
  i_tod_card_soul_bomb_regular.png | face to edit (SOUL BOMB)
  i_tod_card_sticky_c4_regular.png | face to edit (STICKY C4)
  i_tod_card_cluster_regular.png | face to edit (CLUSTER)
  i_tod_card_bash_regular.png | face to edit (BASH)
  i_tod_card_gravity_smash_regular.png | face to edit (CYBER SMASH)
preview: 234x351
-->

# 189 — The card back + rarity-neutral card faces (art request for docs/187)

STATUS: INSTALLED 2026-09-29 (the user generated it anyway: files - 2026-09-29T095001.181.zip). The card back (also docs/191's back) + 13 neutral
faces; originals parked in docs/189_ref/_prev_shipped_20260929/ (NOT git-tracked for some - the only copy).
TodPull OLD_FACES_NEUTRAL = true (covers off). BUILT: FULL BUILD OK 10:24:14 (tmp/card_art/full1.log),
FF 218,962,304 B. This back stays the back of every class still on the old faces; docs/191's back (a
full-bleed silhouette) is installed as i_tod_card2_back for the classes on the layered card.

Repo side (not in the pack): docs/187 THE PULL draws the rarity LIVE (band colour, the
"EPIC +3" words, the level pips) over ONE face per upgrade. Today TodPull.lua paints
covers over the old baked band / pips. When this drop lands:
1. `-Inspect` it, LOOK at every image, proofread.
2. Copy the 13 faces over the same names in `source_data/tod_ui_images/_images/`
   (they keep the `_regular` name on purpose: no GDT / zone / Lua wiring).
3. Add `i_tod_card_back` (GDT block + zone `image,` line) and set `backImage =
   RegisterImage( "i_tod_card_back" )` in tod_upgrade.lua's TodPull.Attach call.
4. In TodPull.lua drop the two covers (`bandRim` stays as the slot edge; `pipCover`
   alpha 0) once every live face is neutral.
5. FULL build; proof = fresh content-hash `.iwi`s.

<!-- PACK:BEGIN -->
# Card back + rarity-neutral card faces

## What this is for
In our game, upgrade cards are now dealt **face down**. The back glows and climbs
through four rarity colours (white, blue, purple, gold), then the card flips. The game
itself draws the rarity on the flipped card: a coloured band with words like
"EPIC +3", and a row of level dots. So:

- the **card back** must be **neutral** (no rarity colour of its own: the game adds the glow), and
- every **card face** must have **no rarity** on it: the band slot and the dot tray are
  left **empty**, because the game fills them in live.

## Deliverables (PNG, RGBA, exact sizes, exact names)

| File | Size | What |
|---|---|---|
| `i_tod_card_back.png` | 768 x 1152 | NEW: the face-down card back |
| `i_tod_card_dmg_reduction_regular.png` | 768 x 1152 | EDIT of the reference with the same name |
| `i_tod_card_bounty_regular.png` | 768 x 1152 | EDIT |
| `i_tod_card_luck_regular.png` | 768 x 1152 | EDIT |
| `i_tod_card_adrenaline_regular.png` | 768 x 1152 | EDIT |
| `i_tod_card_summoning_power_regular.png` | 768 x 1152 | EDIT |
| `i_tod_card_grapple_regular.png` | 768 x 1152 | EDIT |
| `i_tod_card_riot_shield_regular.png` | 768 x 1152 | EDIT |
| `i_tod_card_retriever_regular.png` | 768 x 1152 | EDIT |
| `i_tod_card_soul_bomb_regular.png` | 768 x 1152 | EDIT |
| `i_tod_card_sticky_c4_regular.png` | 768 x 1152 | EDIT |
| `i_tod_card_cluster_regular.png` | 768 x 1152 | EDIT |
| `i_tod_card_bash_regular.png` | 768 x 1152 | EDIT |
| `i_tod_card_gravity_smash_regular.png` | 768 x 1152 | EDIT |

14 files. Keep the file names EXACTLY (including `_regular`).

## Hard rules
1. Exactly **768 x 1152**, RGBA, transparent outside the card's rounded corners (like the references).
2. **The faces are an EDIT, not a redraw.** Frame, title plate and title text, the
   illustration, the description box and its text stay **pixel-identical** to the
   reference of the same name. Change ONLY the three boxed areas in
   `reference/face_remove_these_three.png`:
   - **A. The rarity word band** (the pill reading "REGULAR +1", pixels x 170-598, y 712-775):
     keep the pill's SHAPE and dark outline, but make its inside an **empty flat dark
     slot** (near-black navy, no text, no highlight). The game fills it.
   - **B. The round rarity gem** (the silver star coin at the art window's lower right,
     about x 530-660, y 610-740): **remove it**, and continue the art window's frame and
     illustration background behind it naturally.
   - **C. The level dots** (the five dots at the bottom, x 236-532, y 1000-1060): **remove
     the dots**, leave the **empty dark tray** they sat in. The game draws its own dots.
3. **The back** (`i_tod_card_back.png`) is **neutral**: dark scratched black chrome /
   gunmetal, a thin cool-white edge light, a centred emblem of **a tall cyber spire
   crowned by a floating crown** (our tower), and the words **TOWER OF DOOM II** small
   along the bottom, in our typeface (see the typography rules below). No red, blue,
   purple or gold anywhere. The game tints and glows it in those colours itself. It
   must read as the same card family as the faces (same outer silhouette, same rounded
   corners, same frame thickness).
4. Nothing else. No new text on the faces, no rarity words, no numbers in the band.

## Prompt A — the card back (attach: the three face references)
"A collectible game card BACK, 768x1152, portrait, rounded corners, the same outer
silhouette and frame thickness as the attached cards. Dark scratched black-chrome and
gunmetal surface, subtle diagonal machining, a thin cool white rim light. In the centre
a clean bold emblem: a tall slender cyber spire, stepped, with a floating crown hovering
above its tip and a thin halo ring crossing it. Small along the bottom edge, the words
TOWER OF DOOM II in the attached game typeface. Strictly neutral colours: black, steel
grey, white light only. No red, no blue, no purple, no gold. Clean, bold, readable when
shown at 234x351. Transparent outside the rounded corners."

## Prompt B — each face (attach: face_remove_these_three.png + that card's reference)
"Edit the attached card image. Keep everything pixel-identical EXCEPT three areas:
(1) the pill band reading 'REGULAR +1': keep its shape and outline, make its inside an
empty flat dark navy slot with no text; (2) remove the round silver star coin at the
lower right of the picture window and continue the frame and background behind it;
(3) remove the five dots at the bottom, keeping their empty dark tray. Same size
768x1152, same transparency."

## Delivery checklist
- [ ] 14 PNGs, names exactly as the table, 768 x 1152, RGBA
- [ ] every face: the band is an empty dark slot, no star coin, no dots, and everything else unchanged
- [ ] the back has no rarity colour, and TOWER OF DOOM II is in our typeface
- [ ] zip them flat (no folders)

## Do NOT
- redraw the faces' illustrations or titles
- put any rarity word, number or colour on a face or the back
- change sizes, crop, or add borders/shadows outside the card
<!-- PACK:END -->
