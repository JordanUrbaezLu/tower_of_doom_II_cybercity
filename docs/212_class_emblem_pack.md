# 212 - THE CLASS EMBLEM PACK (2026-10-05)

> **STATUS: GENERATED + STAGED (wave 3, W3C). Not built, not played.** Generator:
> `tools/artgen/packs/w3c_class_pack.py` (`--check` gates the bytes and the wiring once landed).
> Supersedes docs/100 (the Map One medals). The replaced art is parked in `docs/212_ref/_prev_shipped/`.

## Why (user, 2026-10-05)

*"Class icons can be improved and I dont want that red fill on top left. Lets also make them look like they come
from same pack. Might mean making it from scratch but necromancer doesnt look like a consistent design to the
others."* Item 4 of the same message sets the bar for every asset: *"Whole entire asset library should look like
one library."*

What was wrong, measured on the shipped files:
- every `i_tod_class_medallion_*` disc had a red / magenta arc baked over its top-left quarter, and it was a round
  disc inside the R4 octagon ring;
- Archer, Breacher and Warrior were thin tinted line glyphs with no white core; the Necromancer was a filled
  bright-green skull with three crystals breaking out of its ring (a different pack);
- the deal panel's `i_tod_upg_class_*` plates still wore Map One's hazard stripes beside R4's synthwave luck badge.

## The pack

| Piece | Where it draws | Size |
|---|---|---|
| `i_tod_class_medallion_{assault,heavy,slasher,necromancer}` | the local HUD inside `i_tod_h2_medallion_ring` (47 canvas = 70 px at 1080p) and every teammate row (35 canvas = 52 px, no ring) | 512 x 512, compressed high color |
| `i_tod_upg_class_{assault,heavy,slasher,necromancer}` | the upgrade deal panel's CLASS badge, the luck badge's mirror (`tod_upgrade.lua` ClassBadge, 280 x 60 canvas = 1:1) | 420 x 90, uncompressed |

One construction for all four, in the R4 library's grammar (R4's compositor and plate geometry are imported):

- **The medallion** is a black-glass octagon whose edge runs parallel to the HUD ring's inner hairline (so in the
  ring the glass meets the ring band; alone in a teammate row it is a whole badge). It has ONE neon tube in the
  class's identity hue and a faint inner line, like the power-up tokens. The tube's halo is clipped to the glass:
  nothing glows past the octagon, and the outermost pixels carry 0/255 alpha.
- **The symbol** is an R4 neon glyph: white-hot ink for the OBJECT, the class hue for its ENERGY (the one accent),
  a soft hue halo. The rule is "the business end glows":

  | Class | Object (white) | Energy (hue) |
  |---|---|---|
  | ARCHER (`assault`) | a drawn recurve bow and the arrow's shaft | the broadhead and the fletching |
  | BREACHER (`heavy`) | a shotgun shell (brass head, ribs, crimp) | the breaching blast from its crimp, three pellets |
  | WARRIOR (`slasher`) | the cyber sword (fuller, wrapped grip, pommel) | the blade's lit cutting edge |
  | NECROMANCER (`necromancer`) | the skull (cut sockets, nose, teeth) | its eyes and three rising souls |

  The same stroke weights everywhere (34 px primary, 18 px secondary, 12 px cuts at 512). The ink mass of the four
  is measured on every run and held within 0.128..0.167 of the tube's area. Each symbol clears the tube by at least
  23 px.
- **The identity hues** are `tod_class_select.lua`'s `CLASSES[].accent`, the live tint of each class's role and
  weapon text: Archer `#FFBF40`, Breacher `#FF594D`, Warrior `#BF73FF`, Necromancer `#8CFF73`. `--check` fails if
  the Lua and the art drift apart. The Breacher keeps its coral red: it is the class's identity on its draft card
  and in the class select, as Juggernog's red is its perk's (R4). Moving it is a design call that would re-tint the
  card and the select too.
- **The plate** is R4's luck-badge plate with its side edges 4 px in, so its halo stays inside the image. The
  medallion itself sits where the luck badge has its clover well, and `CLASS <NAME>` is set in our typeface in the
  luck badge's text slot (cap 25, the name in neon). The word gap is 2.2 face spaces: the face's own space read as
  "CLASSBREACHER" once the neon halo spread into it.

## Review evidence

`art/generated/W3C-class-pack/`: `_review.png` (OLD vs NEW at full size, at 1080p in the ring and in a teammate
row, the plates at 1:1 and at 2x) and `_review_screens.png` (the HUD's bottom-left at 1080p, and the deal panel
rendered by `tools/ui_mockup/render_pull.py` as each class).

## Not changed

- `i_tod_h2_medallion_ring` (R4): checked. It has no top-left arc: its magenta run is the left-middle-to-bottom
  edge and its cyan run is the top right. It stays as it is.
- The class select cards (`i_tod_card_class_*`), the class terminal (the same menu), the pause menu and scoreboard
  class headers draw no class emblem (the cards show the weapon; the headers are text), so nothing there changes.
