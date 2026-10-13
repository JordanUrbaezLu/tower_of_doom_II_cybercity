# 177 — THE ARCHER: everything still drawn as text or a stand-in (13 images)

<!-- art-pack
name: archer
refs:
  i_tod_card_distraction_regular.png | the CURRENT id-41 card: its ACCENT COLOUR (the Archer's, class-scoped) and slot layout are right; its picture (a cymbal monkey) and its words are WRONG and are replaced by GRAPPLE. Attach to Prompts A and B for the accent only.
  i_tod_card_riot_shield_regular.png | a shipped card in the deck's current chassis: copy the body, title plate, panel, ribbon, value plate and pip row exactly.
  i_tod_card_riot_shield_super.png | the SUPER rarity treatment (purple rails, ribbon, glow, gold medal, 2 lit pips).
  i_tod_card_riot_shield_ultimate.png | the ULTIMATE rarity treatment (gold rails, ribbon, glow, sparkles, 3 lit pips).
  i_tod_pause_r45.png | the pause-menu nameplate style (RIOT SHIELD): copy the pill, notch and lettering exactly with the new words. Attach to Prompt C.
  i_tod_card_class_assault.png | the Archer's class card in the approved FALLEN / BLACKOUT theme: the character, the bow and the palette the new pictures belong to.
  i_tod_hud_gun_enfield.png | a shipped gun HUD cell (the Bow borrows it today): the exact silhouette style, stroke and framing for the three bow cells.
  i_tod_hud_gun_axe.png | a shipped gun HUD cell (the Gold Battle Sword): a second example of the same style.
  docs/99_hud_ref/art_direction_board.png | the art direction for every gun icon: palette, the six rules, good and bad examples. Attach to Prompt D.
  i_tod_hud_off_frag.png | a shipped OFFHAND glyph (the frag): the exact style for the two new offhand glyphs.
  i_tod_hud_off_monkey.png | a shipped OFFHAND glyph (the cymbal monkey): second example of the offhand style.
  model_export/tod_archer/_images/i_tod_archer_hook_hud.png | the grapple HOOK as it exists in the game (a render of the real model): the SUBJECT for the hook glyph, not the style.
  model_export/tod_archer/_images/i_tod_archer_axe_hud.png | HELL'S RETRIEVER as it exists in the game (a render of the real model): the SUBJECT for the axe glyph and the axe card, not the style.
preview: 213x320 300x44 144x66 24x24
-->

> **STATUS: SHIPPED in build 6, FULL BUILD OK 2026-09-26 13:33:44 (fresh content-hash .iwi for all 13 images at 13:33, control untouched). Drop files - 2026-09-26T124431.584.zip, staged art/archer_art/drop_20260926_1244/. UNPLAYED.** User: *"we'll need new assets for each
> one and it should follow the same pattern as the class assets ... zip up
> whatever is remaining for each class in its own zip."* This is the ARCHER's
> zip. Everything in it is drawn as TEXT or as a BORROWED picture today:
>
> | in game today | what the player sees | this brief |
> |---|---|---|
> | GRAPPLE card (id 41, `distraction`) | text fallback (`CARD_SLUG[41]` is off because the old art is the cymbal monkey) | 3 cards + 1 plate |
> | HELL'S RETRIEVER card (id 57, `retriever`) | text fallback, no art at all | 3 cards + 1 plate |
> | Bow / Crossbow / Fire Bow HUD cells | the ENFIELD / KRIG 6 / AK-47 rifle icons (`AetheriumLoadout.lua` TOD_GUN_CAT: cc_bow -> enfield, cc_crossbow -> krig6, cc_fire_bow -> ak47) | 3 gun cells |
> | HOOK / AXE kit tiles | 512x512 model renders squeezed into a 24x24 glyph cell | 2 offhand glyphs |
>
> The class card, both tier cards, the glyph, medallion and name plate are
> DONE (docs/173, FALLEN / BLACKOUT) and are not in this pack.

## Install (when the drop lands)

1. `.\tools\make_art_pack.ps1 -Inspect 'files (N).zip'`; look at every image
   at true size beside its reference; proofread every baked word against the
   glyph set (A-Z 0-9 - ' . / + coin).
2. Copy all thirteen PNGs into `source_data/tod_ui_images/_images/`. `i_tod_pause_r41`
   REPLACES the old DISTRACTION plate under the same name; every other name is
   NEW: an image block each in the UI-image GDT (copy a sibling block: a card
   block for the six cards, the r45 block for r57, the enfield block for the
   three gun cells, the frag block for the two offhand glyphs) and an
   `image,<name>` zone line each.
3. Wire the draw path (an install is not done until the draw path is read):
   - `tod_upgrade.lua`: `CARD_SLUG[41] = "grapple"`, `CARD_SLUG[57] = "retriever"`;
     remove `[41]` from `CoD.TodTextPlate`; raise `PAUSE_PLATE_MAX` 56 -> 57
     (the plates are contiguous; the Breacher's 58-61 and the Warrior's 62/63
     raise it further, whoever installs last owns the number) and re-run
     `node tools/lint_tod_assets.js` (GATE A/B) + its selftest.
   - `AetheriumLoadout.lua`: `[ "cc_bow" ] = "bow"`, `[ "cc_crossbow" ] =
     "crossbow"`, `[ "cc_fire_bow" ] = "firebow"` in TOD_GUN_CAT, the six
     display-name rows (BOW / BOW EX, R1 SHADOWHUNTER / EX, FIRE BOW / EX) to
     the same three keys; `CLASS_KITS[0].imgs = { "i_tod_hud_off_hook",
     "i_tod_hud_off_axe" }`.
   - The scoreboard / start menu draw the plate by id; nothing to change there.
4. FULL build (image assets); proof = a fresh content-hash `.iwi` for every
   new name beside an untouched control. Flip this STATUS to SHIPPED with the
   build.

<!-- PACK:BEGIN -->
# THE ARCHER — two upgrade cards (3 rarities each), two nameplates, three weapon icons, two ability glyphs

The Archer is one of four classes in a zombies map. Every class has a deck
of upgrade cards the player draws from, a row of small weapon icons on the
HUD, and two small ability glyphs beside the weapon. The Archer's two newest
cards and five icons are placeholders. This pack orders the thirteen images.

Everything must match the shipped files in `reference/` exactly in style:
the cards are chunky flat-cartoon on a near-black navy chassis; the weapon
icons are pure white silhouettes; the ability glyphs are white-on-dark
pictograms. `preview_onscreen_*/` shows each reference at the size the player
actually sees it: judge your work at that size.

## Deliverables

| file | size | baked text | pips |
|---|---|---|---|
| `i_tod_card_grapple_regular.png` | 768 x 1152 | title **`GRAPPLE`**, value line **`LONGER ROPE, STRONGER LANDING`** | 3 sockets, **1 lit** |
| `i_tod_card_grapple_super.png` | 768 x 1152 | same | 3 sockets, **2 lit** |
| `i_tod_card_grapple_ultimate.png` | 768 x 1152 | same | 3 sockets, **3 lit** |
| `i_tod_pause_r41.png` | 300 x 44 | **`GRAPPLE`** | — |
| `i_tod_card_retriever_regular.png` | 768 x 1152 | title **`HELL'S RETRIEVER`**, value line **`MORE THROWS, HARDER HITS`** | 3 sockets, **1 lit** |
| `i_tod_card_retriever_super.png` | 768 x 1152 | same | 3 sockets, **2 lit** |
| `i_tod_card_retriever_ultimate.png` | 768 x 1152 | same | 3 sockets, **3 lit** |
| `i_tod_pause_r57.png` | 300 x 44 | **`HELL'S RETRIEVER`** | — |
| `i_tod_hud_gun_bow.png` | 288 x 132 | none | — |
| `i_tod_hud_gun_crossbow.png` | 288 x 132 | none | — |
| `i_tod_hud_gun_firebow.png` | 288 x 132 | none | — |
| `i_tod_hud_off_hook.png` | 128 x 128 | none | — |
| `i_tod_hud_off_axe.png` | 128 x 128 | none | — |

Thirteen files. Every file at exactly the stated size, PNG with alpha, the
file name exactly as written.

## The cards (six files)

### The card template (identical on all three rarities of a card)

Copy `reference/i_tod_card_riot_shield_regular.png` part for part:

1. **Card body**: rounded-corner near-black navy card, very thick black
   outline, faint horizontal scanlines, a small dark cross-head screw in each
   corner, a slim vertical accent rail inside the left and right edges
   (rarity-coloured).
2. **Title plate**: the rounded orange-to-amber gradient plate with a black
   outline and seven small studs along its top edge, holding the title in
   chunky white bubble letters with a heavy dark outline. One line, all caps,
   identical on all three rarities.
3. **Illustration panel**: the rounded darker-navy inset panel with a soft
   radial sheen at the top, faint scanlines, a thin inner border, four tiny
   corner pixel squares and two or three small sparkle glyphs. The picture
   goes inside it.
4. **Rarity ribbon**: the gradient pill with a dark notched arrowhead each
   side, rarity text in the same bubble lettering; the round star medal
   overlapping the panel's bottom-right corner.
5. **Value plate**: the dark inset rectangle with a thin rounded inner frame
   and a rivet in each corner, holding ONE centred line of chunky all-caps
   outlined lettering: the value line from the table. Identical text on all
   three rarities; only its colour changes. No second line, **no number
   anywhere** on the card except the ribbon.
6. **Pip row**: THREE round sockets (these cards have eight levels; the deck
   draws eight-level cards with three sockets), lit left to right per the
   table.

**The accent colour** (the rails, the panel border, the doodles, the value
line's tint on the regular card) is the ARCHER's class colour. Sample it from
`reference/i_tod_card_distraction_regular.png`, which is an Archer-only card
in the same deck. Take ONLY the colour from that file: its picture (a toy
monkey) and its words are being replaced.

### Rarity treatment, the only differences between the three files of a card

| | REGULAR | SUPER | ULTIMATE |
|---|---|---|---|
| side rails, panel border, doodles | the Archer accent | purple/violet (+ a touch of the accent) | gold and red (+ a touch of the accent) |
| rarity ribbon | silver/grey, text `REGULAR +1` | glowing purple, text `SUPER +2` | glowing orange-gold, text `ULTIMATE +3` |
| medal | silver | gold | gold |
| value-line lettering | pale grey-blue | purple/lavender | gold/amber |
| pips lit | 1 | 2 | 3 |

Match `reference/i_tod_card_riot_shield_super.png` and
`reference/i_tod_card_riot_shield_ultimate.png` for the super and ultimate treatments.

### Illustration A: GRAPPLE (same picture on all three rarities)

A chunky flat-cartoon **grapple hook flying on a taut cable** across the
panel: the hook (a compact three-pronged steel claw, dark gunmetal with a
thin cyan edge-light, drawn from `reference/i_tod_archer_hook_hud.png`'s
shape) in the upper right, biting into the corner of a dark ledge; the cable
running down and left in a slight sag to a small wrist launcher at the lower
left edge (a gloved forearm entering from the panel edge, the launcher a
squat cylinder strapped over the wrist). The archer's body is NOT shown:
only the forearm. Between the two ends, three short motion streaks along
the cable's direction and a small burst of dust at the hook's bite. Below
the forearm, near the bottom of the panel, a small **landing shockwave**
glyph: two concentric half-rings on the ground in the accent colour, the
"strong landing" idea. No faces, no zombies, no text or digits inside the
panel.

### Illustration B: HELL'S RETRIEVER (same picture on all three rarities)

A chunky flat-cartoon **flying tomahawk** filling the centre of the panel,
drawn from `reference/i_tod_archer_axe_hud.png`'s shape: a short dark
wooden-and-steel handle, a broad single-edged axe head whose EDGE GLOWS
DEEP RED (ember-orange core, red bloom), the axe tilted and spinning
(three short curved motion arcs behind it). A thin **red chain of ember
sparks** trails from the handle's end in a loop that curls back toward the
lower left corner of the panel: the axe returns to the hand. In the lower
left, a gloved open hand (palm up, forearm entering from the panel edge)
waiting for it. In the upper background, two or three small dark zombie
silhouettes (heads and shoulders only, no faces) already cut, drawn as
plain dark shapes with a red edge-light so they read as "hit" without gore.
No blood, no digits, no text inside the panel.

## The nameplates (two files)

`reference/i_tod_pause_r45.png` is the exact style: a slim dark pill with a
notch, chunky outlined lettering, 300 x 44, on transparency. Make two, with
the words **`GRAPPLE`** and **`HELL'S RETRIEVER`** (the apostrophe is in our
typeface). Same pill, same lettering size and colour, same left margin; the
longer name may run closer to the right notch, never past it.

## The weapon icons (three files)

The HUD draws a small pure-white silhouette of the weapon in hand. Draw the
three bows in exactly the style of `reference/i_tod_hud_gun_enfield.png` and
`reference/i_tod_hud_gun_axe.png`, following
`reference/art_direction_board.png` (attach it to every prompt):

| file | the weapon | the one identifying feature to make BIG |
|---|---|---|
| `i_tod_hud_gun_bow.png` | a compact modern recurve BOW seen from the side, string drawn slightly, an arrow nocked | the curved limbs and the string |
| `i_tod_hud_gun_crossbow.png` | a stocky tactical CROSSBOW seen from the side, stock to the left, limbs to the right, a bolt in the rail | the horizontal limbs across a rifle-like stock |
| `i_tod_hud_gun_firebow.png` | the FIRE BOW: the same bow silhouette with a heavier, ornamented riser and a flame-shaped arrowhead | the flame-shaped head and the runic riser |

Rules, from the reference set: pure white silhouette with dark cut-lines on
transparency; no colour, no gradient, no glow, no outline halo, no background
plate; same stroke weight as the references (put yours beside the enfield at
the same size and compare); the object spans most of the width, centred
vertically, a small margin on every side, nothing touching the edges; one
object per cell; no hands, no motion lines, no text; all three face the same
way (arrow / bolt pointing RIGHT).

## The ability glyphs (two files)

Beside the weapon the HUD shows two 24 x 24 tiles, one per ability, drawn
from 128 x 128 sources. `reference/i_tod_hud_off_frag.png` (a grenade) and
`reference/i_tod_hud_off_monkey.png` (a toy monkey) are the exact style:
a simple white pictogram with a thin dark outline, filling most of the
square, readable at 24 x 24. Make two:

| file | the pictogram |
|---|---|
| `i_tod_hud_off_hook.png` | the grapple HOOK: a three-pronged claw pointing UP, a short length of cable curling below it. Subject from `reference/i_tod_archer_hook_hud.png`. |
| `i_tod_hud_off_axe.png` | HELL'S RETRIEVER: the tomahawk head-up, tilted 20 degrees, a small ember dot at the tip of the edge (the ONE allowed non-white element: a single red-orange dot). Subject from `reference/i_tod_archer_axe_hud.png`. |

Look at `preview_onscreen_24x24/` for the frag and monkey at their true
size: if your glyph is not readable at that size, simplify it.

## Prompts (paste-ready)

Attach the named references to each.

**Prompt A, GRAPPLE regular card** (attach `i_tod_card_riot_shield_regular.png`,
`i_tod_card_distraction_regular.png`, `i_tod_card_class_assault.png`,
`i_tod_archer_hook_hud.png`): "A 768x1152 collectible upgrade card in the
exact chassis of the attached riot shield card: near-black navy rounded body
with a thick black outline, scanlines, corner screws, coloured side rails,
an orange-amber studded title plate reading GRAPPLE in chunky white bubble
letters with a dark outline, a darker inset illustration panel, a silver
REGULAR +1 ribbon with a silver star medal, a riveted value plate reading
LONGER ROPE, STRONGER LANDING in pale grey-blue outlined caps, and three
round pip sockets with the first lit. Accent colour sampled from the
attached monkey card's rails. Inside the panel: a chunky flat-cartoon
three-pronged steel grapple hook biting a dark ledge in the upper right, a
taut sagging cable running to a wrist launcher on a gloved forearm at the
lower left, three motion streaks, a dust burst at the bite, and two
concentric half-ring shockwave lines on the ground below in the accent
colour. No body, no face, no zombies, no text inside the panel."

**Prompt B, HELL'S RETRIEVER regular card** (attach the same chassis
references and `i_tod_archer_axe_hud.png`): "Same chassis and treatment as
the attached riot shield card; title plate HELL'S RETRIEVER, value plate
MORE THROWS, HARDER HITS in pale grey-blue outlined caps, silver REGULAR +1
ribbon and medal, three pip sockets with the first lit, accent colour
sampled from the attached monkey card's rails. Inside the panel: a chunky
flat-cartoon spinning tomahawk filling the centre, dark handle, broad
single-edged head whose edge glows deep red with an ember-orange core,
three curved motion arcs, a looping trail of red ember sparks curling back
to an open gloved hand at the lower left, and two or three plain dark
zombie silhouettes with a red edge-light in the upper background. No blood,
no faces, no text inside the panel."

**Prompts A2/A3 and B2/B3** (attach the finished regular card plus
`i_tod_card_riot_shield_super.png` or `i_tod_card_riot_shield_ultimate.png`): "Apply the attached
SUPER (or ULTIMATE) rarity treatment to the attached finished card: rails,
panel border and doodles recoloured, the ribbon reading SUPER +2 (or
ULTIMATE +3) with its glow, gold medal, the value line in purple/lavender
(or gold/amber), two (or three) pips lit. Change nothing else."

**Prompt C, the two nameplates** (attach `i_tod_pause_r45.png`): "Two
300x44 nameplates in exactly the style of the attached: same dark pill,
notch, lettering size and colour, reading GRAPPLE and HELL'S RETRIEVER."

**Prompt D, the three weapon icons** (attach `i_tod_hud_gun_enfield.png`,
`i_tod_hud_gun_axe.png`, `art_direction_board.png`): "Flat white silhouette
icons on transparency, 288x132 each, same line weight and framing as the
attached rifle icon, dark cut-lines only, no colour or glow: (1) a compact
modern recurve bow seen from the side with an arrow nocked, (2) a stocky
tactical crossbow seen from the side with a bolt in the rail, (3) a heavier
ornamented fire bow with a runic riser and a flame-shaped arrowhead. Arrow
and bolt point right."

**Prompt E, the two ability glyphs** (attach `i_tod_hud_off_frag.png`,
`i_tod_hud_off_monkey.png`, `i_tod_archer_hook_hud.png`,
`i_tod_archer_axe_hud.png`): "Two 128x128 white pictograms with a thin dark
outline on transparency, in the style of the attached grenade and monkey
glyphs, simple enough to read at 24x24: (1) a three-pronged grapple claw
pointing up with a short curl of cable below, (2) a tomahawk head-up tilted
20 degrees with a single red-orange ember dot at the edge tip."

## Checklist before you send

- [ ] 13 files, names exactly as in the table, sizes exactly as stated, PNG with alpha
- [ ] card chassis matches the riot shield card part for part; only the panel picture, the title, the value line and the rarity treatment differ
- [ ] the six cards carry NO number except the ribbon's +1 / +2 / +3
- [ ] value line identical across a card's three rarities, colour per the table
- [ ] nameplates: same pill, notch, lettering as r45
- [ ] weapon icons: white on transparent only, same stroke weight as the enfield, facing right
- [ ] glyphs readable at 24x24 (compare in `preview_onscreen_24x24/`)
- [ ] every baked word uses only the characters in `typography/`

## Do NOT

- do not redraw or resend any reference file
- do not keep the toy monkey, or any monkey, anywhere
- do not put numbers, percentages or level counts on a card
- do not add colour, glow or a background to the weapon icons
- do not draw the archer's face or body on any card; a gloved forearm or hand is the most that appears
<!-- PACK:END -->
