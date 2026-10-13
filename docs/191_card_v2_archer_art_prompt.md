<!-- art-pack
name: card_v2_archer
refs:
  docs/191_ref/card2_layout_template.png | THE LAYOUT, exact pixels: every region every layer must respect. Attach to EVERY prompt.
  docs/191_ref/look_target_prototype_common_epic.png | THE LOOK TARGET (a live prototype the owner approved): a white COMMON card and a purple EPIC card side by side. Match this structure and mood, just richer and hand-painted. Attach to Prompts A, B, C.
  docs/191_ref/look_target_prototype_rare.png | the same prototype with two blue RARE cards. Attach to Prompts A and B.
  i_tod_card_luck_regular.png | the CURRENT card: the illustration style (chunky outlines, starfield window, bold readable icon) is the style for every illustration. Attach to Prompt F.
  i_tod_card_grapple_regular.png | current GRAPPLE card: keep its subject, redraw it for the new window. Attach to Prompt F (grapple).
  i_tod_card_retriever_regular.png | current HELL'S RETRIEVER card: keep its subject. Attach to Prompt F (retriever).
  i_tod_card_dmg_reduction_regular.png | current DMG REDUCTION card: keep its subject. Attach to Prompt F (dmg_reduction).
  i_tod_card_bounty_regular.png | current BOUNTY card: keep its subject. Attach to Prompt F (bounty).
  i_tod_card_tier_assault_2.png | current Archer TIER 2 card: the R1 SHADOWHUNTER crossbow is its subject. Attach to Prompt F (tier 2).
  i_tod_card_tier_assault_3.png | current Archer TIER 3 card: the FIRE BOW is its subject. Attach to Prompt F (tier 3).
  i_tod_card_class_assault.png | the Archer class card, for the class's look (bows, hood, green/teal accents). Attach to Prompt F.
preview: 234x351
-->

# 191 — Card v2 (the layered card) + every Archer card (art request)

STATUS: INSTALLED 2026-09-29 10:27 (the user's drop `files - 2026-09-29T100040.213.zip`: all 22
files, exact names and sizes, 0 layout warnings, back strictly neutral, TOWER OF DOOM II spelled
right). The drop's back was installed as **`i_tod_card2_back`** (the layered card's full-bleed
silhouette); the docs/189 back stays `i_tod_card_back` for the classes still on the old faces
(its silhouette sits 50 px in, like them). The PACK section below now names the back
`i_tod_card2_back.png`. CARD V2 IS PER CLASS (the installer lists a class in the manifest's
`classes` only when every card it can be dealt has its art, read from the live game script):
the ARCHER is the one complete class. Rendered with tools/ui_mockup/render_pull.py (Archer
LEGENDARY/EPIC/RARE/COMMON + the TIER 2 card; a Warrior hand stays on the old cards + old back).
Next: the same layers for the other three classes need only their 6 illustrations + tier 2/3
each (DR / LUCK / BOUNTY, the frames, crests, body, back and banner are shared).
docs/189's "edit the old faces" task was a separate, earlier pack (installed the same day).

Repo side (not in the pack): user 2026-09-28/29 - "Looks pretty bland without UI", "doesn't
look like the artifact", "change our card design in general so that it works with this new
system ... all upgrade cards for archer first". THE CARD IS NOW LAYERS, drawn by the game:
illustration (per upgrade) -> body (neutral, with a see-through art window) -> rarity frame
(per rarity: trim + title plate + ornaments, MORE ORNATE THE RARER) -> rarity crest -> live
text in our typeface (title, two short lines, the "EPIC +3" band, the level pips). No text is
baked into any card layer, so a card's words can never go stale again. Install: copy the PNGs
into `source_data/tod_ui_images/_images/`, run `python tools/card_pull/install_card_art.py`
(adds GDT blocks + zone lines + the generated Lua manifest), FULL build.

<!-- PACK:BEGIN -->
# Card v2: the layered upgrade card + all Archer cards

## What this is for
In our zombies game you pick upgrade cards. Cards are dealt face down, the back glows and
climbs through four RARITY colours, then the card flips:

| Rarity | Colour | RGB |
|---|---|---|
| COMMON | white / silver | 233, 238, 245 |
| RARE | blue | 58, 168, 255 |
| EPIC | purple | 181, 92, 255 |
| LEGENDARY | gold | 255, 194, 61 |

The game now BUILDS each card from separate layers and writes all the text itself. So this
request is a set of LAYERS, not finished cards. The look to hit is the attached prototype
(`look_target_prototype_*.png`): same structure, but hand-painted, richer, more premium.

## Deliverables - 22 PNGs, RGBA, exact sizes and names

| File | Size | What |
|---|---|---|
| `i_tod_card2_body.png` | 768 x 1152 | the card BODY, rarity-neutral (see rules) |
| `i_tod_card2_frame_common.png` | 768 x 1152 | COMMON frame overlay (silver/white) |
| `i_tod_card2_frame_rare.png` | 768 x 1152 | RARE frame overlay (blue) |
| `i_tod_card2_frame_epic.png` | 768 x 1152 | EPIC frame overlay (purple) |
| `i_tod_card2_frame_legendary.png` | 768 x 1152 | LEGENDARY frame overlay (gold) |
| `i_tod_card2_crest_common.png` | 144 x 144 | COMMON crest gem |
| `i_tod_card2_crest_rare.png` | 144 x 144 | RARE crest gem |
| `i_tod_card2_crest_epic.png` | 144 x 144 | EPIC crest gem |
| `i_tod_card2_crest_legendary.png` | 144 x 144 | LEGENDARY crest gem |
| `i_tod_card2_back.png` | 768 x 1152 | the face-down card BACK |
| `i_tod_pull_banner.png` | 1024 x 192 | a ribbon banner, WHITE (the game tints it) |
| `i_tod_card2_art_dmg_reduction.png` | 576 x 448 | illustration: DMG REDUCTION |
| `i_tod_card2_art_bounty.png` | 576 x 448 | illustration: BOUNTY |
| `i_tod_card2_art_luck.png` | 576 x 448 | illustration: LUCK |
| `i_tod_card2_art_deadeye.png` | 576 x 448 | illustration: DEADEYE |
| `i_tod_card2_art_piercing.png` | 576 x 448 | illustration: PIERCING |
| `i_tod_card2_art_sprint.png` | 576 x 448 | illustration: SPRINT |
| `i_tod_card2_art_quick_draw.png` | 576 x 448 | illustration: QUICK DRAW |
| `i_tod_card2_art_grapple.png` | 576 x 448 | illustration: GRAPPLE |
| `i_tod_card2_art_retriever.png` | 576 x 448 | illustration: HELL'S RETRIEVER |
| `i_tod_card2_art_tier_assault_2.png` | 576 x 448 | illustration: TIER 2, the R1 SHADOWHUNTER crossbow |
| `i_tod_card2_art_tier_assault_3.png` | 576 x 448 | illustration: TIER 3, the FIRE BOW |

## Hard rules (all layers)
1. Exact sizes above, PNG, RGBA. Every size is already a multiple of 4 - keep it.
2. **NO TEXT anywhere** except the words TOWER OF DOOM II on the card back. The game draws
   every title, number and description itself.
3. **The layout is exact.** `card2_layout_template.png` gives every region in pixels on the
   768 x 1152 canvas. The BODY and all FOUR FRAMES must line up pixel-for-pixel: same outer
   silhouette, same rounded corners (radius about 56), same window, same slots.
4. Transparent (alpha 0) outside the card's rounded corners on body, frames and back.

## Layer A - the BODY (`i_tod_card2_body.png`)
The card's dark base. Rarity-NEUTRAL: dark navy / gunmetal, subtle machined panel texture,
a soft inner shadow. It contains:
- the **ART WINDOW** (96,176 to 672,624) as a **fully TRANSPARENT HOLE** with a thin dark
  bevel around it (the illustration shows through from behind);
- the **BAND SLOT** (168,656 to 600,724): an EMPTY dark rounded pill, recessed;
- the **TEXT PANEL** (88,752 to 680,972): an EMPTY dark recessed panel with a thin line border;
- the **PIP TRAY** (184,996 to 584,1068): an EMPTY dark recessed tray;
- the **CREST SOCKET**: a round recess 144 wide centred at (640,576), overlapping the art
  window's bottom-right corner (inside the socket is dark, the crest sits on it).
No colour accents on the body (the frame brings the colour). No title plate on the body.

## Layer B - the four RARITY FRAMES (`i_tod_card2_frame_<rarity>.png`)
An overlay drawn ON TOP of the body. Transparent everywhere except: the outer trim, the
**TITLE PLATE** (64,36 to 704,148, an EMPTY plate - the game writes the title on it in
dark lettering, so the plate must be light/saturated), thin trim around the art window,
thin trim around the band slot, and corner ornaments. It must NOT cover the inside of the
art window, band slot, text panel, pip tray or crest socket.
**THE RARER, THE MORE ORNATE** - a player must tell rarities apart by SHAPE, not only colour:
- **COMMON**: plain brushed-silver trim, simple flat silver-white title plate. Clean.
- **RARE**: blue chrome trim, a glossy blue title plate, small studs at the four corners.
- **EPIC**: purple crystal trim with glowing edges, a violet title plate with small crystal
  wings at its ends, a gem in each corner.
- **LEGENDARY**: ornate GOLD filigree trim, a gold title plate crowned by a small crown with
  wings, glowing amber gems in the corners, fine engraved scrollwork. The most premium item
  in the game; unmistakable even in a glance.
All four share exactly the same silhouette and keep-clear zones.

## Layer C - the four CRESTS (`i_tod_card2_crest_<rarity>.png`, 144 x 144)
A gem emblem that sits in the crest socket AND is shown small (20 px) on a rarity ladder beside
the card, so it must read at tiny size: bold silhouette, strong colour. Transparent background.
COMMON a round silver gem; RARE a faceted blue diamond; EPIC a purple star-cut crystal;
LEGENDARY a gold crown-gem with a bright core. Same visual family, rising in complexity.

## Layer D - the CARD BACK (`i_tod_card2_back.png`)
The face-down back, same silhouette as the body. Dark scratched black chrome / gunmetal,
subtle diagonal machining, a thin cool-white rim light, a centred emblem of a tall stepped cyber
spire with a floating crown above its tip and a thin halo ring crossing it, and the words
TOWER OF DOOM II small along the bottom in the attached game typeface. STRICTLY NEUTRAL: black,
steel grey, white light. No red, blue, purple or gold - the game glows it in those colours.

## Layer E - the BANNER (`i_tod_pull_banner.png`, 1024 x 192)
A wide ribbon / plaque that flashes across a card when it flips; the game writes "EPIC" and
"+3 LEVELS" on it and TINTS it to the rarity colour. So paint it in WHITE and light greys
only (shading in greys, highlights white), with a darker centre strip for the words, swallowtail
ends. Transparent background. No text.

## Layer F - the 11 ILLUSTRATIONS (576 x 448 each)
Each fills the whole art window (full bleed, background included). Style = the attached current
cards: chunky dark outlines, bold simple readable subject, deep blue starfield window background
with a few sparkles, plus a soft neon rim light. Keep a 24 px margin on every side free of
important detail (the window bevel covers it) and keep the **bottom-right 150 x 150 corner**
free of the subject (the crest covers it). Subject centred, big, readable at 176 x 136 on screen.
Subjects:
- `dmg_reduction` - a glowing hexagon energy shield deflecting bullets (match the current card's subject).
- `bounty` - a stack of gold coins and a bulging money bag (match the current card).
- `luck` - a four-leaf clover with a gold coin (match the current card).
- `deadeye` - a drawn bow with a glowing crosshair eye on the arrowhead.
- `piercing` - one arrow punching straight through three green zombie heads in a row.
- `sprint` - a running boot with speed streaks and a small dust burst.
- `quick_draw` - a bow mid-draw with motion ghosts of three arrows and a small stopwatch.
- `grapple` - a wrist-mounted grappling launcher firing its hook and cable (match the current card).
- `retriever` - Hell's Retriever: a flaming spiked tomahawk mid-spin (match the current card).
- `tier_assault_2` - the R1 SHADOWHUNTER heavy crossbow, three-quarter view, teal accents.
- `tier_assault_3` - the FIRE BOW: a lava-veined bow with glowing orange cracks and embers.

## Prompts
**Prompt A - body** (attach `card2_layout_template.png`, `look_target_prototype_common_epic.png`, `look_target_prototype_rare.png`): "A collectible game card BODY
layer, 768x1152 PNG with alpha, rounded corners. Dark navy and gunmetal machined panel, subtle
texture and inner shadow, no bright colour. It has a fully transparent rectangular window at
96,176 to 672,624 with a thin dark bevel; an empty recessed dark pill at 168,656 to 600,724; an
empty recessed dark panel at 88,752 to 680,972; an empty recessed tray at 184,996 to 584,1068;
a round dark socket 144 wide centred at 640,576. No text, no title plate. Transparent outside
the rounded corners. Follow the attached layout template exactly."

**Prompt B - frames** (attach `card2_layout_template.png`, `look_target_prototype_common_epic.png`,
`look_target_prototype_rare.png`; make COMMON first, then derive the other three from it so they align): "A card FRAME overlay, 768x1152 PNG, transparent except
the outer trim, a title plate at 64,36 to 704,148, thin trims around the window 96,176 to
672,624, around the pill 168,656 to 600,724, and corner ornaments. Rarity <COMMON silver /
RARE blue chrome / EPIC purple crystal / LEGENDARY ornate gold filigree with a small winged crown
on the title plate>. The plate is empty (no text). Everything inside the window, pill, lower
panels and the 144 px socket at 640,576 stays fully transparent."

**Prompt C - crests** (attach `look_target_prototype_common_epic.png`): "A rarity crest gem icon, 144x144 PNG,
transparent background, bold and readable at 20 pixels: <COMMON round silver gem / RARE faceted
blue diamond / EPIC purple star-cut crystal / LEGENDARY gold crown-gem with a bright core>."

**Prompt D - back** (attach `card2_layout_template.png` for the silhouette, `i_tod_card_class_assault.png` for the finish): as Layer D above.

**Prompt E - banner**: as Layer E above.

**Prompt F - illustrations** (always attach `i_tod_card_luck_regular.png` for the style, plus the
subject's current card when it has one: `i_tod_card_dmg_reduction_regular.png`, `i_tod_card_bounty_regular.png`,
`i_tod_card_grapple_regular.png`, `i_tod_card_retriever_regular.png`, `i_tod_card_tier_assault_2.png`
(crossbow), `i_tod_card_tier_assault_3.png` (fire bow); for the four NEW subjects also attach
`i_tod_card_class_assault.png` for the Archer's look): "An illustration
for a collectible game card, 576x448, full bleed. Chunky dark outlines, bold simple readable
subject, deep blue starfield background with a few sparkles, soft neon rim light, in the exact
style of the attached card's picture. Subject: <subject>. Keep the bottom-right 150x150 corner
clear of the subject and a 24 px margin clear of detail. No text."

## Delivery checklist
- [ ] 22 PNGs, exact names and sizes, RGBA
- [ ] body + 4 frames line up pixel-perfect (lay them over the layout template to check)
- [ ] window, pill, panels, tray and socket are transparent/empty where the template says
- [ ] no text anywhere except TOWER OF DOOM II on the back, in our typeface
- [ ] zip them flat (no folders)

## Do NOT
- bake titles, rarity words, numbers, dots or descriptions into any layer
- colour the body or the back with a rarity colour
- move or resize any region of the layout template
<!-- PACK:END -->
