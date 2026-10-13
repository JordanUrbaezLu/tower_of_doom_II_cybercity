# 178 — BREACHER: every remaining piece of art (3 upgrade cards, 3 pause plates, 2 grenade icons, 3 gun icons)

<!-- art-pack
name: breacher
refs:
  i_tod_card_fire_rate_regular.png | THE UPGRADE CARD STYLE, REGULAR rarity: chassis, title bar, art window, rarity ribbon, description panel, pips. Match it exactly.
  i_tod_card_mage_ice_super.png | the same chassis at SUPER rarity: how the frame, coin, ribbon and pip colour change for SUPER. Its pip row has 5 sockets; the new cards have THREE.
  i_tod_card_fire_rate_ultimate.png | the same chassis at ULTIMATE rarity: the gold frame, glow, sparkles and three lit pips.
  i_tod_pause_r53.png | THE PAUSE-MENU ROW PLATE: a 300x44 bar with the card name on it. Match it exactly.
  i_tod_pause_r55.png | a second pause-menu row plate, for the layout of a longer name.
  i_tod_hud_off_blink.png | THE GRENADE / ABILITY ICON STYLE (128x128): flat shapes, dark outline, one accent colour. Match it.
  i_tod_hud_off_frag.png | the frag grenade icon the C4 borrows today: same style; the new C4 and Cluster icons sit where this one sits.
  i_tod_hud_gun_spas12.png | THE GUN ICON STYLE (288x132): pale silhouette, dark outline, chunky cut details. The 870 borrows this cell today.
  i_tod_hud_gun_executioner.png | the gun icon the Mozambique borrows today: same style.
  i_tod_hud_gun_mog12.png | the gun icon the Peacekeeper borrows today: same style.
  docs/99_hud_ref/art_direction_board.png | the art direction for every gun icon: palette, the six rules, good and bad examples.
preview: 234x351 300x44 36x36 144x66
-->

> **STATUS: SHIPPED in build 6 (FULL BUILD OK 2026-09-26 13:33:44 Eastern, FF 189,722,752 B): all 17 images in the linker ledger. UNPLAYED. REQUESTED 2026-09-26.** The Breacher's three new upgrade cards
> (PELLETS 58, STICKY C4 60, CLUSTER 61; CHANGELOG 2026-09-26) draw as TEXT
> today (no `CARD_SLUG` row, no pause plate), the C4 and Cluster tiles borrow
> the frag glyph and the Hellbound thermite icon, and all three Breacher guns
> borrow another gun's HUD cell (`AetheriumLoadout.lua` TOD_GUN_CAT:
> cc_mozambique -> executioner, cc_rem870 -> spas12, cc_peacekeeper -> mog12).
> The class / tier / glyph / medallion / plate art is already THEME B (docs/173
> drop, installed 2026-09-25) and is NOT in this pack. The C4's missing
> stick / armed cue is a SOUND and is not in this pack either.
>
> None of the three cards has a dark lane (`set_no_dark` on all three), so there
> are no `_dark` cards or plates. The upgrade cards follow the UPGRADE CARD set
> (the style every other card in the deal wears), not the class theme.

## Install (when the drop lands)

1. `.\tools\make_art_pack.ps1 -Inspect 'files (N).zip'`: look at every image at
   true size beside its reference; proofread the baked text (only A-Z 0-9 - ' . / +).
2. Copy all 17 PNGs into `source_data/tod_ui_images/_images/`. All are NEW names:
   - Cards: `CARD_SLUG[58] = "pellets"`, `[60] = "sticky_c4"`, `[61] = "cluster"`
     in `tod_upgrade.lua`; an image block per file in the UI images GDT (copy a
     card block); `image,` zone lines for the nine cards.
   - Pause plates: GDT block + zone line each for `i_tod_pause_r58/r60/r61`.
   - Grenade icons: `CLASS_KITS[2].imgs` in `AetheriumLoadout.lua` becomes
     `{ "i_tod_hud_off_cluster", "i_tod_hud_off_c4" }`; GDT + zone line each.
   - Gun cells: TOD_GUN_CAT `cc_mozambique -> "mozambique"`, `cc_rem870 -> "rem870"`,
     `cc_peacekeeper -> "peacekeeper"` plus the display-name rows (MOZAMBIQUE /
     MOZAMBIQUE HERE, REMINGTON 870 MCS / REFITTED-870 ..., PEACEKEEPER /
     PEACEMAKER); GDT + zone line each.
   Cards, zone and Lua are SHARED files: tell the lead first.
3. `lint_tod_assets` (GATE A catches a named-but-unzoned image), then a FULL
   build; proof = fresh content-hash `.iwi` for the new names beside an untouched
   control. Flip this STATUS to SHIPPED with the build.

<!-- PACK:BEGIN -->
# BREACHER art: 3 upgrade cards, 3 menu plates, 2 grenade icons, 3 gun icons

The Breacher is the close-range shotgun class: it kicks the door in with a
shotgun and clears the room with sticky C4 and a cluster grenade. Seventeen
images are missing for it. Every one has a shipped reference in `reference/`
that it must match exactly in style, size and framing.

## Deliverables (17 PNG files, transparent background unless stated)

### A. Upgrade cards: 768 x 1152 each, 9 files

Same chassis as `reference/i_tod_card_fire_rate_regular.png` (REGULAR),
`reference/i_tod_card_mage_ice_super.png` (SUPER) and
`reference/i_tod_card_fire_rate_ultimate.png` (ULTIMATE): title bar, art window,
rarity coin, rarity ribbon, description panel, the row of pips. Only the TITLE, the
ART in the window and the DESCRIPTION change between cards; the frame, ribbon,
coin and pips follow the rarity exactly as in the references.

PIPS: ALL NINE CARDS carry exactly THREE round sockets in the pip row (as on
`reference/i_tod_card_fire_rate_regular.png`). The rarity lights them:

| rarity | pips | ribbon | side rails, panel border, doodles | value-line lettering | medal | outer glow |
|---|---|---|---|---|---|---|
| REGULAR | 1 lit white, 2 dark | silver/grey, `REGULAR +1` | cyan | pale grey-blue | silver | none |
| SUPER | 2 lit purple-white, 1 dark | glowing purple, `SUPER +2` | purple/violet | purple/lavender | gold | soft lavender glow round the card edge |
| ULTIMATE | 3 lit gold | glowing orange-gold, `ULTIMATE +3` | gold and red | gold/amber | gold | warm gold-and-pink glow plus small gold sparkle crosses outside the border |

Take every one of these from the three reference cards. Nothing else changes
between the rarities: the title, the window art and the value line are identical.
The value line is ONE centred line with NO number in it.

| file | title bar | ribbon | description | art in the window |
|---|---|---|---|---|
| `i_tod_card_pellets_regular.png` | PELLETS | REGULAR +1 | MORE PELLETS PER BLAST | a pump shotgun firing, a wide cone of round pellets spraying out of the muzzle, many pellets clearly counted |
| `i_tod_card_pellets_super.png` | PELLETS | SUPER +2 | MORE PELLETS PER BLAST | same art as regular |
| `i_tod_card_pellets_ultimate.png` | PELLETS | ULTIMATE +3 | MORE PELLETS PER BLAST | same art as regular |
| `i_tod_card_sticky_c4_regular.png` | STICKY C4 | REGULAR +1 | MORE CHARGES - BIGGER BLAST | a brick of C4 (a grey block wrapped in tape, a small detonator with a blinking red light and two wires) stuck to a surface, a small remote detonator beside it |
| `i_tod_card_sticky_c4_super.png` | STICKY C4 | SUPER +2 | MORE CHARGES - BIGGER BLAST | same art as regular |
| `i_tod_card_sticky_c4_ultimate.png` | STICKY C4 | ULTIMATE +3 | MORE CHARGES - BIGGER BLAST | same art as regular |
| `i_tod_card_cluster_regular.png` | CLUSTER | REGULAR +1 | MORE CLUSTERS - BIGGER BLAST | a canister grenade bursting open in mid-air, five or six small round bomblets flying out of it on arcs, each with a lit sparking fuse |
| `i_tod_card_cluster_super.png` | CLUSTER | SUPER +2 | MORE CLUSTERS - BIGGER BLAST | same art as regular |
| `i_tod_card_cluster_ultimate.png` | CLUSTER | ULTIMATE +3 | MORE CLUSTERS - BIGGER BLAST | same art as regular |

### B. Pause-menu row plates: 300 x 44 each, 3 files

Exactly like `reference/i_tod_pause_r53.png`: the same bar, the same cyan end
cap, the name in the same letters, left-aligned the same way.

| file | text on the plate |
|---|---|
| `i_tod_pause_r58.png` | PELLETS |
| `i_tod_pause_r60.png` | STICKY C4 |
| `i_tod_pause_r61.png` | CLUSTER |

### C. Grenade icons: 128 x 128 each, 2 files

Exactly the style of `reference/i_tod_hud_off_blink.png` and
`reference/i_tod_hud_off_frag.png`: flat shapes, a thick dark outline, one
strong accent colour, centred with a small margin. They are shown small
(about 36 pixels on a 1080p screen), so the shape must read at a glance.

| file | what it shows | accent |
|---|---|---|
| `i_tod_hud_off_c4.png` | a C4 brick seen at an angle: a block with tape bands, a small detonator box on top with one bright red light | red light |
| `i_tod_hud_off_cluster.png` | a squat cylindrical canister grenade with three small round bomblets bursting out of its top | orange fuse sparks |

### D. Gun icons: 288 x 132 each, 3 files

Exactly the style of `reference/i_tod_hud_gun_spas12.png`: a pale blue-white
silhouette with a thick dark outline and chunky cut-in details, on
transparency, the gun seen from the side with the muzzle pointing RIGHT,
spanning most of the width, centred vertically. Follow
`reference/art_direction_board.png`.

| file | the gun | the one feature that must read |
|---|---|---|
| `i_tod_hud_gun_mozambique.png` | MOZAMBIQUE: a compact triple-barrel shotgun PISTOL (a pistol grip, a short chunky frame, three stacked barrel openings at the muzzle) | the three barrels at the muzzle |
| `i_tod_hud_gun_rem870.png` | REMINGTON 870: a classic pump-action shotgun with a full stock, a long tube magazine under the barrel and a ribbed pump grip | the ribbed pump under the barrel |
| `i_tod_hud_gun_peacekeeper.png` | PEACEKEEPER: a futuristic lever-action energy shotgun, a boxy angular body, a wide flat muzzle, a lever loop behind the trigger | the wide flat muzzle and the lever loop |

## Hard rules

- Every file exactly the size in its table, PNG with transparency.
- Match the references. Put your image beside its reference at the same size;
  if the line weight, outline or chassis differs, redo it.
- Card text only as listed; the only characters available are A-Z, 0-9 and
  - ' . / + (no commas, no ampersands, no exclamation marks).
- The three rarities of one card share the SAME window art; only the frame,
  coin, ribbon and pips change.
- Gun icons face RIGHT. Grenade icons have no text.
- No watermarks, no signatures, no extra backgrounds on the icons and plates.

## Prompts (paste-ready)

1. CARDS (attach `reference/i_tod_card_fire_rate_regular.png`,
   `reference/i_tod_card_mage_ice_super.png`, `reference/i_tod_card_fire_rate_ultimate.png`):
   "Game upgrade card, 768x1152, exactly the same card frame, title bar, art
   window, rarity ribbon, description panel and pips as the attached card at
   <RARITY> rarity. Title bar text '<TITLE>'. Ribbon text '<RIBBON>'.
   Description text '<DESCRIPTION>'. Art in the window: <ART>. Same cartoon
   style with thick dark outlines, same dark blue scanline background in the
   window."
2. PLATES (attach `reference/i_tod_pause_r53.png` and `reference/i_tod_pause_r55.png`): "Menu row plate, 300x44,
   identical to the attached plate, with the text '<TEXT>' in the same letters
   and position."
3. GRENADE ICONS (attach `reference/i_tod_hud_off_blink.png`,
   `reference/i_tod_hud_off_frag.png`): "Flat game HUD icon, 128x128,
   transparent background, same style as the attached icons (flat colour
   shapes, thick dark outline): <WHAT IT SHOWS>."
4. GUN ICONS (attach `reference/i_tod_hud_gun_spas12.png`, `reference/i_tod_hud_gun_executioner.png`, `reference/i_tod_hud_gun_mog12.png`,
   `reference/art_direction_board.png`): "Game HUD weapon icon, 288x132,
   transparent background, same style as the attached icon (pale blue-white
   silhouette, thick dark outline, chunky cut-in details), side view with the
   muzzle pointing right: <THE GUN>. Make <THE FEATURE> clearly visible."

## Checklist before you send

- [ ] 17 files, names exactly as in the tables
- [ ] cards 768x1152, plates 300x44, grenade icons 128x128, gun icons 288x132
- [ ] every card's title, ribbon and description spelled exactly as listed
- [ ] the three rarities of each card share one window art
- [ ] every card has exactly three pip sockets, 1 / 2 / 3 lit by rarity
- [ ] gun icons face right; icons and plates on transparency
- [ ] each image checked beside its reference at the same size

## Do NOT

- do not redraw or resend any reference image
- do not add numbers to the cards other than the ribbon's +1 / +2 / +3
- do not make dark / corrupted versions of the cards (these have none)
- do not put hands, characters or explosions around the gun icons
<!-- PACK:END -->
