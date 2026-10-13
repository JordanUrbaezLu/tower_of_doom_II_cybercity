# 217 - The card chrome and the reel's rarity, in the synthwave library (R10, 2026-10-05)

User 2026-10-05: *"Whole entire asset library should look like one library."* The W3F audit
(`tmp/wave3/W3F-library-audit`, findings F03 + F06) found two families still speaking collectible-card-game
metal beside the R3/R4 synthwave chrome:

- **F03, the layered upgrade card (THE PULL, every card deal).** Polished silver / blue / violet / gold rims, a
  glossy bright header pill, baroque filigree and a winged crown on LEGENDARY, glossy 3D gem crests, and a
  soft-rendered grey card back.
- **F06, the Black Market reel.** Gold baroque scrolls on the LEGENDARY tile (and so on the CURSED tile cut from
  it), lightning squiggles on the EPIC tile, and electric wisps on the EPIC stamp.

## The rule: rarity escalates with LIGHT, never ornament

| Rarity | Hue (tod_upgrade.lua RARITY) | Card frame |
|---|---|---|
| COMMON | white / silver (233, 238, 245) | one rim tube |
| RARE | blue (58, 168, 255) | + bracket corners (the second tube at the four corners only) |
| EPIC | violet (181, 92, 255) | a double tube all the way round + a few sparks |
| LEGENDARY | gold (255, 194, 61) | double tube + heavier brackets + a neon crown on the header + embers + a stronger halo |

The hues are the Lua's RARITY colours to the byte (the game tints the glow, the ladder and the band ground with
them). The generator's `--check` re-reads them.

## What changed

All of it is drawn by **`tools/artgen/packs/r10_card_chrome.py`**, built on `synthwave.py` and R4's compositor.
The names and sizes are unchanged, so there is no wiring.

- **`i_tod_card2_body`**: a chamfered black-violet glass plate. Its corners are cut top-left / bottom-right 60 and
  top-right / bottom-left 24. The body, all four frames and the back share ONE silhouette, so a card never changes
  size on the flip.
  - The art window is cut through it, with a 22 px chamfer top-left.
  - The crest socket is a chamfered octagon well.
  - The band slot, text panel and pip tray are chamfered recesses with steel lips.
- **`i_tod_card2_frame_<rarity>` x 4**: a steel-glass bezel carrying the rim tube(s), and a DARK-glass header
  plate whose label well matches the LUI title label exactly. Also a window tube that runs round the crest
  socket (one outline), a band ring, and the rarity's light from the table above.
- **`i_tod_card2_crest_<rarity>` x 4**: white-hot neon tokens with a hue accent and halo. COMMON is a round
  brilliant (table, star and girdle cuts), RARE a diamond (half its facets blue), EPIC an eight-point star (one face
  of each point violet), LEGENDARY a crown (gold band, white-hot jewel). They read at the ladder's 27 px.
- **`i_tod_card2_back`**: the spire as neon line-art on black glass. It has a synthwave sun with slits, a
  perspective grid floor, the city on the horizon, a halo ring, the crown and TOWER OF DOOM II in our typeface.
  It is STRICTLY NEUTRAL: the installer's neutrality rule passes, and TodPull's BackTint washes it in each rung's
  colour as it climbs.
- **`i_tod_pull_pill`** (the title label and rarity band quad, `tools/card_pull/install_card_art.py fx_pill`):
  chamfered top-left / bottom-right instead of a rounded capsule. `PILL_CUT_V` / `_H` is LOCKSTEP with the
  generator's `PILL_CUT`, and `--check` reads the sprite back.
- **The reel** (cut from the previous shipped art, parked in `docs/217_ref/_prev_shipped/`; scrolls, squiggles and
  wisps removed by a harmonic (Laplace) fill over each ornament's own field; frame lines re-run down their columns):
  - **`i_tod_spin_tile_legendary`**: the four scrolls removed. Neon brackets on the inner line's corners, small
    glints on the frame, a few embers.
  - **`i_tod_spin_tile_epic`**: the two squiggles removed, four sparks added.
  - **`i_tod_spin_banner_epic`**: the wisps and the six nubs removed, sparks on both ends.
  - **`i_tod_spin_tile_cursed`**: `tools/dealer_house/make_spin_art.py` re-run on the new legendary tile, with no
    script change. The brackets and embers turn blood red and bone.
  - The LEGENDARY stamp has no ornament (its glints are already light), so it and the CURSED stamp are unchanged.
- **`i_tod_card_back` is retired whole.** Every class has been layered since 2026-09-29, so the old back only ever
  drew for a class with no v2 faces, and none exists. Its GDT block, zone line and TodCardArt.lua row are removed,
  and its PNG is in `archive/map1_carryover/`. TodPull's `BuildBack` / `BackPick` already take `back2` when `back`
  is nil.

## Geometry kept (asserted by `--check`, measured against the parked shipped art, tolerance 2.5 px)

| Opening | Where |
|---|---|
| Art window | hole (96,176)-(671,623); window tube inner edges L 93 / R 674 / T 173 / B 626 |
| Crest socket | centred (640,576); ring outer edges R 721 / B 657 |
| Band ring | inner edges L 164-165 / R 602 / T 652-653 / B 726 |
| Title label | TodPull V2.titleLabel x 768/234 = (80.4,50.9)-(687.6,129.6), read from the Lua |

The socket's lower-left cut is deeper (56) so that its tube keeps 12.7 px from the band ring's top-right corner. The
shipped rings touched there.

## White text reads (WCAG, white on the ground under it)

| Rarity | label top | label foot | bare well | band slot |
|---|---|---|---|---|
| COMMON | 8.0 | 9.7 | 13.6 | 19.8 |
| RARE | 12.0 | 13.6 | 16.2 | 20.0 |
| EPIC | 13.7 | 15.1 | 17.0 | 20.0 |
| LEGENDARY | 9.6 | 11.3 | 14.6 | 20.0 |

Every ground clears 7:1. "Bare well" is the frame's own label well if the LUI label ever failed to draw.

## Gates

- `python tools/artgen/packs/r10_card_chrome.py --check` checks:
  - bytes;
  - the openings above;
  - the hue / label / window / socket lockstep with the Lua;
  - the pill's chamfer;
  - the installer's own keep-clear / see-through / neutral-back rules;
  - the contrast floor;
  - the GDT / zone wiring;
  - the old back retired.
- `install_card_art.py --check` (presence + size + layout) and `make_spin_art.py --check` pass on the landed tree.

## Reviews

- `art/generated/R10-card-chrome/_review.png`: OLD | NEW at 1:1 for every rarity's stacked card, the bare body
  and the back.
- `art/generated/R10-card-chrome/_review_parts.png`: the crests, the pill, the reel tiles and the stamp.
- `art/generated/R10-card-chrome/_review_screens.png`: the real Lua (`render_pull.py`, `render_spin.py`).

These are renders and mocks: the in-game look is the user's playtest.
